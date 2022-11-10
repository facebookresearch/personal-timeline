import torch
import numpy as np
import pickle
import datetime
import os

from src.persistence.personal_data_db import PersonalDataDBConnector
from collections import Counter
from tqdm import tqdm

from typing import Dict, List, Union
from src.objects.LLEntry_obj import LLEntry, LLEntrySummary
from src.util import distance
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
from src.enrichment import socratic
from src.util import is_home, get_location_attr, geo_cache, geolocator, default_location, str_to_location
from geopy import Location

from pillow_heif import register_heif_opener
register_heif_opener()


class LLImage:
    def __init__(self,
                 img_path: str,
                 time: int,
                 loc: Location):
        """Create an image object from LLEntry and run enhencements
        """
        self.img_path = img_path
        self.img = None
        self.embedding = None
        self.places = []
        self.objects = []
        self.tags = []
        self.enhance()
        # release memory
        del self.img

        self.time = time
        self.loc = loc

    def enhance(self, k=5):
        """Run enhencements.
        """
        if not os.path.exists(self.img_path + ".compressed.jpg"):
            # RGBA -> RGB
            if self.img == None:
                self.img = Image.open(self.img_path)
            self.img = ImageOps.exif_transpose(self.img)
            self.img = self.img.convert("RGB")
            self.img.save(self.img_path + ".compressed.jpg")

        # CLIP embeddings and zero-shot image classification
        model_dict = socratic.model_dict
        drop_gpu = socratic.drop_gpu

        with torch.no_grad():
            if os.path.exists(self.img_path + ".emb"):
                image_features = pickle.load(open(self.img_path + ".emb", "rb"))
            else:
                if self.img == None:
                    self.img = Image.open(self.img_path)
                image_input = model_dict['clip_preprocess'](self.img).unsqueeze(0).to(model_dict['device'])
                image_features = model_dict['clip_model'].encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                pickle.dump(image_features, open(self.img_path + ".emb", "wb"))

            sim = (100.0 * image_features @ model_dict['openimage_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            openimage_classes = [model_dict['openimage_classnames'][idx] for idx in indices]

            sim = (100.0 * image_features @ model_dict['tencentml_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            tencentml_classes = [model_dict['tencentml_classnames'][idx] for idx in indices]

            sim = (100.0 * image_features @ model_dict['place365_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            self.places = [model_dict['place365_classnames'][idx] for idx in indices]

            self.objects = openimage_classes + tencentml_classes

            # simple tagging for food, animal, person, vehicle, building, scenery, document, commodity, other objects
            sim = (100.0 * image_features @ model_dict['simple_tag_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            tag = [model_dict['simple_tag_classnames'][idx] for idx in indices][0]
            if tag == 'other objects':
                self.tags = []
            else:
                self.tags = [tag]

        self.embedding = image_features.squeeze(0).cpu().numpy()



def create_image_summary(images: List[LLImage], k=3):
    """Create a k-image summary using k-means
    """
    if len(images) < k:
        return [img.img_path for img in images]

    X = np.array([img.embedding for img in images])
    kmeans = KMeans(n_clusters=k, random_state=42).fit(X)
    centers = [c / np.linalg.norm(c) for c in kmeans.cluster_centers_]
    nearest = [None for _ in range(k)]
    best_sim = [-1.0 for _ in range(k)]

    for img, label in zip(images, kmeans.labels_):
        sim = np.dot(img.embedding, centers[label])
        if sim > best_sim[label]:
            best_sim[label] = sim
            nearest[label] = img

    return [img.img_path for img in nearest if img is not None]


def postprocess_bloom(answer: str, keywords: List[str]=None):
    """Postprocess a bloom request response."""
    # answer = answer.replace('\n', ',').replace('-', ',').replace('.', ',')
    # items = [item.strip() for item in answer.split(',')]
    # items = list(Counter([item for item in items if len(item) >= 5]).keys())
    # return items
    # print(answer)
    if isinstance(answer, bytes):
        answer = answer.decode('UTF-8')
    answer = answer.replace('"', '').replace("'", '')
    answer = answer.strip().split('\n')[0]
    
    # none answer
    if keywords is not None and "Keywords:" in answer:
        print('Bad:', keywords)
        answer = keywords[0]

    return answer


def summarize_activity(entries: List[LLImage]):
    """Classify activity of a segment by sending a query to Bloom"""
    objects_cnt = Counter()
    places_cnt = Counter()

    for ent in entries:
        for o in ent.objects[:1]:
            objects_cnt[o] += 1
        for p in ent.places:
            places_cnt[p] += 1

    sorted_places = list(zip(*places_cnt.most_common(3)))[0]
    object_list = ', '.join(list(zip(*objects_cnt.most_common(10)))[0])
    loc = get_location(entries)
    city = get_location_attr(loc, ["town", "city", "suburb", "county"])

    if city.strip() == "":
        tags = []
    else:
        tags = [city]
        
    tags += object_list.split(', ') + list(sorted_places)
    keyword_prompt = f"Keywords: {', '.join(tags)}"
    print(keyword_prompt)

    # prompt = "I am an intelligent image captioning bot. I am going to describe the activities in photos. "
    # prompt += f"I think these photos were taken in {city} at a {sorted_places[0]} or {sorted_places[1]}. "
    # prompt += f"I think there might be a {object_list} in these photos. "
    # prompt += "A short and creative caption to describe these photos. tl;dr:"
    # print(prompt)
    prompt = open('src/enrichment/socratic/caption_prompt.txt').read()
    prompt += '\n' + keyword_prompt + '\nTitle:'

    response = socratic.generate_captions(prompt, method="Sample")

    # print(prompt)
    # print(response)
    return postprocess_bloom(response, tags)


def summarize_day(day: List[List[LLImage]], activity_index: Dict):
    """Summarize a day given summaries of activities"""
    objects_cnt = Counter()
    places_cnt = Counter()
    activity_summaries = [activity_index[get_timestamp(activity[0])].textDescription for activity in day]

    for activity in day:
        for ent in activity:
            for o in ent.objects[:1]:
                objects_cnt[o] += 1
            for p in ent.places:
                places_cnt[p] += 1

    sorted_places = list(zip(*places_cnt.most_common(3)))[0]
    object_list = ', '.join(list(zip(*objects_cnt.most_common(10)))[0])
    summaries = ' '.join(activity_summaries)

    loc = get_location(day)
    loc = get_location_attr(loc, ["town", "city", "suburb", "county"])

    if loc.strip() == "":
        tags = []
    else:
        tags = [loc]
        
    tags += object_list.split(', ') + list(sorted_places)
    keyword_prompt = f"Keywords: {', '.join(tags)}"
    print(keyword_prompt)

    # prompt = "I am an intelligent image captioning bot. I am going to summarize what I did today. "
    # if loc.strip() != "":
    #     prompt += f"I spent today at {loc}. "
    # prompt += f"I have been to {sorted_places[0]} or {sorted_places[1]}. I saw {object_list}. "
    # if len(activity_summaries) > 1:
    #     prompt += f"I did the following things: {summaries} "
    # prompt += "A short and creative caption for the photos (tl;dr):"

    # print(prompt)
    # prompt = f"""I am an intelligent image captioning bot.
    #   I am going to summarize what I did today.
    #   I spent today at {get_location(day).replace(';', ', ')}.
    #   I have been to {sorted_places[0]}, {sorted_places[1]}, or {sorted_places[2]}.
    #   Today, I saw {object_list}.
    #   A creative short caption I can generate to describe these photos is:"""

    # print(prompt)
    prompt = open('src/enrichment/socratic/caption_prompt.txt').read()
    prompt += '\n' + keyword_prompt + '\nTitle:'

    response = socratic.generate_captions(prompt, method="Sample")

    return postprocess_bloom(response, tags)


def trip_data_to_text(locations: List[Location], start_date: List, num_days: int):
    """Data to text for a trip."""
    loc_cnt = Counter()

    for loc in locations:
        value = get_location_attr(loc, ["town", "city", "county", "suburb", "state", "country"])
        if len(value) > 0:
            loc_cnt[value] += 1

    if len(loc_cnt) == 0:
        return f"""A {num_days}-day trip, {start_date.year}"""
    else:
        place = loc_cnt.most_common(1)[0][0]
        return f"""A {num_days}-day trip to {place}, {start_date.year}"""

    # prompt = f"""Paraphrase "A {num_days}-day trip to {", ".join(loc_str[:1])} in {start_date.year}/{start_date.month}" in proper English:"""
    # print(prompt)
    # response = socratic.generate_captions(prompt, method="Greedy")
    # return postprocess_bloom(response)


def organize_images_by_tags(images: List[LLImage]):
    """Generate an index from image tags (food, plant, etc.) to lists of images."""
    result = {}
    for image in images:
        for tag in image.tags:
            if tag not in result:
                result[tag] = []
            result[tag].append({"img_path": image.img_path, 
                                "name": image.objects[0], 
                                "datetime": datetime.datetime.fromtimestamp(image.time),
                                "location": image.loc})

    return result

previous_location = str_to_location(default_location)

def get_location(segment) -> Location:
    """Computer the location of an LLEntry/LLImage/activity/day"""
    global previous_location
    if isinstance(segment, LLEntry):
        entry = segment

        for loc in entry.locations:
            if loc is not None and loc.address != 'Soul Buoy':
                previous_location = loc
                return loc

        for lat_lon in entry.lat_lon:
            lat_lon = tuple(lat_lon)
            if lat_lon is not None and lat_lon != (0.0, 0.0):
                if lat_lon in geo_cache:
                    previous_location = geo_cache[lat_lon]
                    return geo_cache[lat_lon]
                else:
                    loc = geolocator.reverse(lat_lon)
                    geo_cache[lat_lon] = loc
                    previous_location = loc
                    return loc

        return previous_location
        # if hasattr(entry, "startGeoLocation") and entry.startGeoLocation is not None:
        #     return entry.startGeoLocation
        # else:
        #     return str_to_location(", ".join([entry.startCity, entry.startState, entry.startCountry]))
    elif isinstance(segment, LLImage):
        return segment.loc
    elif isinstance(segment, list):
        # return a location in most frequent city
        city_cnt = Counter()
        loc_dict = {}
        for entry in segment:
            loc = get_location(entry)
            city = get_location_attr(loc, ["town", "city", "suburb", "county"])
            city_cnt[city] += 1
            loc_dict[city] = loc
        most_common_city = city_cnt.most_common(1)[0][0]
        return loc_dict[most_common_city]
    else:
        return ""

def get_start_end_location(segment):
    """Computer start/end locations of a segment"""
    start = get_location(segment[0])
    end = get_location(segment[-1])
    return start, end

def get_timestamp(obj):
    """Return the start timestamp of a LLEntry or a list of LLEntries.
    Convert startTime into usnix time."""
    # 2018-11-25 12:19:01-08:00
    if isinstance(obj, LLEntry):
        return datetime.datetime.fromisoformat(obj.startTime).timestamp()
    if isinstance(obj, LLImage):
        return obj.time
    else:
        return get_timestamp(obj[0])

def create_segments(entries: List[LLImage]):
    """Create segments of the timeline"""
    # create segments of activities
    entries.sort(key=lambda x: get_timestamp(x))

    def segment(entries, eps):
        """Segment a list of events. The parameter eps defines the (expected) length of the segment."""
        clusters = []

        curr_point = entries[0]
        curr_cluster = [curr_point]
        for point in entries[1:]:
            if get_timestamp(point) <= get_timestamp(curr_point) + eps:
                curr_cluster.append(point)
            else:
                clusters.append(curr_cluster)
                curr_cluster = [point]
            curr_point = point
        clusters.append(curr_cluster)
        return clusters

    # create activity segments
    activity_segments = segment(entries, 1800) # 30-minute

    # deduplicate each segment
    for activity in activity_segments:
        if not isinstance(activity[0], LLImage):
            continue
        new_segment = []
        for i, entry in enumerate(activity):
            duplicate = False
            emb_i = activity[i].embedding
            for j in range(i):
                emb_j = activity[j].embedding
                sim = np.dot(emb_i, emb_j)
                if sim > 0.9:
                    duplicate = True
                    break

            if not duplicate:
                new_segment.append(entry)

        activity.clear()
        activity += new_segment


    # create day segments
    day_segments = segment(activity_segments, 43200) # 12-hours

    trip_segments = [[day_segments[0]]]
    prev_is_home = True

    for i in range(len(day_segments)):
        loc = get_location(day_segments[i])
        if is_home(loc):
            trip_segments.append([day_segments[i]])
        else:
            if prev_is_home:
                trip_segments.append([day_segments[i]])
            else:
                if get_timestamp(day_segments[i]) >= get_timestamp(trip_segments[-1][-1]) + 43200 * 2 * 3: # 3-day gap ==> consider a new trip
                    trip_segments.append([day_segments[i]])
                else:
                    trip_segments[-1].append(day_segments[i])
        prev_is_home = is_home(loc)

    return trip_segments

def convert_LLEntry_LLImage(entries: List[LLEntry]):
    """Convert a list of LLEntries to LLImages
    """
    image_entries = []
    tabular_entries = []

    for entry in tqdm(entries):
        time = get_timestamp(entry)
        loc = get_location(entry)

        if entry.imageFilePath is not None and \
           len(entry.imageFilePath) > 0 and \
            os.path.exists(entry.imageFilePath):
            try:
                image_entries.append(LLImage(entry.imageFilePath, time, loc))
            except:
                print("Error when processing image:" + entry.imageFilePath)
        else:
            # TODO: ignoring tabular entries for now
            pass
    return image_entries, tabular_entries


def create_trip_summary(entries: List[LLEntry]):
    """Compute a trip summary from a list of LLEntries.

    Args:
        entries (List[LLEntry]): all LLEntries within the trip

    Returns:
        Dictionary: a JSON object summarizing the trip
    """
    ## Step 1: convert LLEntries to LLImages
    print("Step 1: convert LLEntries to LLImages")
    converted_entries, tabular_db = convert_LLEntry_LLImage(entries)

    ## Step 2: identify activities, days, and trips
    print("Step 2: identify activities, days, and trips (also deduplicate)")
    segments = create_segments(converted_entries)

    ## Step 3: process activities
    print("Step 3: process activities")
    activity_index = {}
    all_activities = []
    for segment in segments:
        for day in segment:
            all_activities += day

    for activity in tqdm(all_activities):
        start_time = get_timestamp(activity[0])
        start_time_str = datetime.datetime.fromtimestamp(start_time)
        end_time = get_timestamp(activity[-1])
        end_time_str = datetime.datetime.fromtimestamp(end_time)

        location = get_location(activity)
        activity_summary = LLEntrySummary(type="activity", 
                                          startTime=start_time_str.isoformat(),
                                          endTime=end_time_str.isoformat(),
                                          locations=[location],
                                          text_summary="%d:00 to %d:00, %s" % (start_time_str.hour, end_time_str.hour, start_time_str.strftime("%B %d, %Y")), # summarize_activity(activity),
                                          photo_summary=create_image_summary(activity),
                                          stats={"num_photos": len(activity)},
                                          objects=organize_images_by_tags(activity),
                                          source="derived")

        activity_index[start_time] = activity_summary

    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    for activity in list(activity_index.values()):
        if activity.stats['num_photos'] >= 3:
            pp.pprint(vars(activity))
            # visualize(activity['photo_summary'])

    ## Step 4: process days
    print("Step 4: process days")
    daily_index = {}
    all_days = []
    for segment in segments:
        all_days += segment
    for day in tqdm(all_days):
        start, end = get_start_end_location(day)
        if start == end:
            locations = [start]
        else:
            locations = [start, end]

        date_str = datetime.datetime.fromtimestamp(get_timestamp(day)).date()
        day_summary = LLEntrySummary(type="day", 
                                     startTime=date_str.isoformat(),
                                     endTime=date_str.isoformat(), # should be the next day?
                                     locations=locations,
                                     text_summary=date_str.strftime("%B %d, %Y"), # summarize_day(day, activity_index),
                                     photo_summary=create_image_summary(sum(day, [])),
                                     stats={"num_photos": sum([len(act) for act in day]),
                                            "num_activities": len(day)},
                                     objects=organize_images_by_tags(sum(day, [])),
                                     source="derived")

        daily_index[date_str] = day_summary

    # pretty print the results
    for day in list(daily_index.values()):
        if day.stats['num_photos'] >= 3:
            pp.pprint(vars(day))
            # visualize(day['photo_summary'])

    ## Step 5: process trips (segments)
    print("Step 5: process trips")
    trip_index = {}
    for segment in tqdm(segments):
        loc = get_location(segment[0])
        total_photos = 0

        # if the segment is a trip
        if not is_home(loc):
            start_date = datetime.datetime.fromtimestamp(get_timestamp(segment[0]))
            start_date_str = start_date.date()
            end_date = datetime.datetime.fromtimestamp(get_timestamp(segment[-1]))
            end_date_str = end_date.date()
            itinerary = []
            locations = []
            photo_summary = []

            i = 0
            while i < len(segment):
                loc = get_location(segment[i])
                locations.append(loc)
                start_index = i
                date_str = datetime.datetime.fromtimestamp(get_timestamp(segment[i])).date()
                itin_entry = {'location': loc, 'start': date_str, 'end': date_str}
                while i+1 < len(segment) and get_location(segment[i+1]) == loc:
                    i += 1
                itin_entry['end'] = datetime.datetime.fromtimestamp(get_timestamp(segment[i])).date()
                end_index = i
                segment_photos = sum(sum(segment[start_index:end_index+1], []), [])
                total_photos += len(segment_photos)
                itin_entry['photo_summary'] = create_image_summary(segment_photos)
                if len(photo_summary) == 0:
                    photo_summary = itin_entry['photo_summary']
                itinerary.append(itin_entry)
                i += 1

            num_days = (end_date.date() - start_date.date()).days + 1

            # TODO: handle itinerary
            trip_summary = LLEntrySummary(type="trip", 
                                     startTime=start_date_str.isoformat(),
                                     endTime=end_date_str.isoformat(),
                                     locations=locations,
                                     text_summary=trip_data_to_text(locations, start_date, num_days),
                                     photo_summary=photo_summary,
                                     stats={"num_photos": total_photos,
                                            "days": num_days},
                                     objects={},
                                     source="derived")

            trip_index[start_date_str] = trip_summary

    for trip in list(trip_index.values()):
        pp.pprint(vars(trip))

    return activity_index, daily_index, trip_index


if __name__ == '__main__':
    db = PersonalDataDBConnector()
    res = db.search_personal_data(select_cols="enriched_data", where_conditions={"enriched_data": "is not NULL"})
    entries = []
    for row in res.fetchall():
        entry = pickle.loads(row[0])
        entries.append(entry)

    entries.sort(key=lambda x: get_timestamp(x))
    entries = entries# [:50]
    activity_index, daily_index, trip_index = create_trip_summary(entries)

    pickle.dump(activity_index, open("activity_index.pkl", "wb"))
    pickle.dump(daily_index, open("daily_index.pkl", "wb"))
    pickle.dump(trip_index, open("trip_index.pkl", "wb"))
