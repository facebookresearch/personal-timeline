import pickle
import sys
import os
import datetime
from matplotlib.image import thumbnail
import matplotlib.pyplot as plt
import matplotlib
import json
import urllib.parse
import geopy
import pytz

from typing import Dict, List, Tuple
from tqdm import tqdm
from PIL import Image
from pillow_heif import register_heif_opener
from geopy import Location
import geopy.distance

from src.objects.LLEntry_obj import LLEntrySummary, LLEntry
from src.persistence.personal_data_db import PersonalDataDBConnector
register_heif_opener()

matplotlib.use('Agg')

map_api_key = os.getenv("GOOGLE_MAP_API")


class TimelineRenderer:

    def __init__(self, path='./'):
        """Rendering timeline JSON object for TimelineJS
        """
        self.activity_index = pickle.load(open(os.path.join(path, 'activity_index.pkl'), 'rb'))
        self.daily_index = pickle.load(open(os.path.join(path, 'daily_index.pkl'), 'rb'))
        self.trip_index = pickle.load(open(os.path.join(path, 'trip_index.pkl'), 'rb'))
        self.img_cache = {}
        self.geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
        self.geo_cache = {}
        self.user_info = json.load(open("user_info.json"))
        self.home_address = self.geolocator.geocode(self.user_info["address"])

    def visualize_images(self, image_paths: List[str]):
        """visualize a list of images
        """
        signature = '_'.join([os.path.split(path)[1] for path in image_paths])
        if signature not in self.img_cache:
            path = "images/summary_%s.png" % (signature)
            self.img_cache[signature] = path
        else:
            path = self.img_cache[signature]

        if os.path.exists(path):
            return path

        plt.figure(figsize=(100,50))
        columns = 9
        for i, img_path in enumerate(image_paths[:9]):
            img = Image.open(img_path)
            plt.subplot(len(image_paths) // columns + 1, columns, i + 1)
            plt.imshow(img)
            plt.axis('off')

        plt.savefig(path, bbox_inches='tight')
        plt.close()
        return path

    def get_city_country(self, location: Location):
        """Get city, state, and country (or "Home") from location
        """
        # TODO: dig deeper to find a better fix
        if location is None:
            return []

        if 'address' not in location.raw or "country" not in location.raw['address']:
            coord = (location.latitude, location.longitude)
            if coord in self.geo_cache:
                location = self.geo_cache[coord]
            else:
                location = self.geolocator.reverse(coord)
                self.geo_cache[coord] = location

        def is_home(loc: Location, home: Location):
            """Check if a location is home (within 100km)."""
            return geopy.distance.geodesic((home.latitude, home.longitude),
               (loc.latitude, loc.longitude)).km <= 100.0

        res = []
        if is_home(location, self.home_address):
            res.append("Home")

        # add one of the 4
        for attr in ["town", "city", "county", "suburb"]:
            if 'address' in location.raw and attr in location.raw['address']:
                res.append(location.raw['address'][attr])
                break

        for attr in ["state", "country"]:
            if 'address' in location.raw and attr in location.raw['address']:
                res.append(location.raw['address'][attr])

        if len(res) == 0:
            return [location.address.split(', ')[-1]]
        else:
            return res


    def create_map_link(self, location: Location):
        """Generate a google map iframe.
        """
        location_list = self.get_city_country(location)
        location = " ".join(location_list)
        link = f'<iframe width="600" height="450" style="border:0" loading="lazy" allowfullscreen src="https://www.google.com/maps/embed/v1/place?key={map_api_key}&q={urllib.parse.quote(location)}"></iframe>'
        # print(link)
        return link

    def convert_date(self, date: str, hour=None):
        """Reformating dates."""
        dt = datetime.datetime.fromisoformat(date)
        if hour == 24:
            dt += datetime.timedelta(days=1)
            hour = 0

        if hour is not None:
            return {'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': hour}
        else:
            return {'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour}

    def create_text(self, headline, text):
        return {"headline": headline, "text": text}

    def objects_to_text(self, object_dict: Dict):
        """Convert a object dictionary to text.
        """
        text = ""
        for tag in object_dict:
            text += f"<p>These are the {tag} that I saw: <ul><li>"
            itemized = []
            for item in object_dict[tag]:
                img_path = item["img_path"] + '.compressed.jpg'
                name = item["name"]
                _, tail = os.path.split(img_path)
                if not os.path.exists(os.path.join('images/', tail)):
                    os.system('cp "%s" images/' % (img_path))

                # itemized.append(f'<a href="{img_path}">{name}</a>')
                itemized.append(f'''<div class="tooltip"><a href="images/{tail}">{name}</a>
                               <span class="tooltiptext">
                               <img src="images/{tail}" alt="image" height="200" /></span>
                               </div>''')
            text += ", ".join(itemized) + " </li> </ul>"


        return text

    def organize_tags(self, objects: Dict, locations: List[str]):
        """Create a 2-level tag lists.
        """
        top = []
        bottom = []

        if objects is not None:
            top += list(objects.keys())
            for item_list in objects.values():
                for item in item_list:
                    bottom.append(item['name'])

        if len(locations) > 0:
            if "Home" in locations:
                top.append("Home")
            top.append(locations[-1])
            bottom += locations[:-1]

        return top, bottom

    def create_summary_tree(self):
        """Assign uid's to each summary and build the tree structure.
        """
        parent = {}
        children = {}

        edges = [] # child to parent edges
        for activity in self.activity_index.values():
            uid = self.get_uid(activity)
            parent_id = f"day_{self.convert_date(activity.startTime, 0)}"
            edges.append((uid, parent_id))
            parent[uid] = ""

        for day in self.daily_index.values():
            uid = self.get_uid(day)
            parent[uid] = ""

        for trip in self.trip_index.values():
            uid = self.get_uid(trip)
            current_day = datetime.datetime.fromisoformat(trip.startTime)
            end_time = datetime.datetime.fromisoformat(trip.endTime)

            while current_day <= end_time:
                child_id = f"day_{self.convert_date(current_day.isoformat(), 0)}"
                edges.append((child_id, uid))
                current_day += datetime.timedelta(days=1)
            parent[uid] = ""


        for uid, vid in edges:
            parent[uid] = vid
            if vid not in children:
                children[vid] = []
            children[vid].append(uid)

        return parent, children


    def get_uid(self, summary: LLEntrySummary):
        """Return a unique ID of a summary
        """
        if summary.type == 'activity':
            ts = self.convert_date(summary.startTime)
        elif summary.type == 'day' or summary.type == 'trip':
            ts = self.convert_date(summary.startTime, 0)
        else:
            raise ValueError("Not supported summary type")

        text = '_'.join(str(item) for item in [ts['year'], ts['month'], ts['day'], ts['hour']])

        return f"{summary.type}_{text}"

    def summary_to_card(self, summary: LLEntrySummary):
        """Convert a LLEntrySummary to a HTML card
        """
        uid = self.get_uid(summary)
        link = f'summary_{uid}.html'
        img_path = summary.image_paths[0] + '.compressed.jpg'
        if summary.startTime == summary.endTime:
            summary_time = summary.startTime
        else:
            summary_time = f"{summary.startTime} - {summary.endTime}"

        new_img_path = 'images/' + os.path.split(img_path)[-1]
        if not os.path.exists(new_img_path):
            os.system('cp "%s" images/' % (img_path))

        card = f"""<div class="card"><a href="{link}">
                   <header class="header-image">
      <div class="header-image-background" style="background-image: url({new_img_path});"></div>
      </header></a><article><p class="dateline">
      <time>
      {summary_time}</time></p>
      <a href="{link}"><h3>{summary.textDescription}</h3></a>
      </article></div>"""
        return card

    def create_cards(self, summaries: List[LLEntrySummary]):
        """Generate a list of cards for search results
        """
        cards = []
        for entry in summaries:
            cards.append(self.summary_to_card(entry))
        return cards

    def entry_to_text(self, entry: LLEntry):
        """Convert an LLEntry to text and tags.
        """
        default_values = ['', '0', '1', '{}']
        text = ""
        tags = []
        for attr in ['purchase_id', 'productName', 'productPrice', 'currency',
        'productQuantity', 'author', 'artist', 'track', 'playtimeMs',
        'track_count', 'duration', 'distance', 'calories', 'outdoor', 'temperature']:
            value = getattr(entry, attr)
            value = str(value)
            if value not in default_values:
                text += f"<p> {attr} : {value} </p>"
                tags.append(value)
        return text, tags

    def load_and_display_LLEntries(self, query_time_range: Tuple[datetime.datetime]=None):
        """Visualize non-image LLEntries
        """
        db = PersonalDataDBConnector()
        # TODO: change the query to select all non-photo LLEntries
        res = db.search_personal_data(select_cols="enriched_data",
                                      where_conditions={"enriched_data": "is not NULL"})
        entries = []
        for row in res.fetchall():
           entry = pickle.loads(row[0])
           entries.append(entry)

        # for testing
        test_entry = LLEntry("testing", "2018-08-30T00:05:23", "testing")
        test_entry.textDescription = "Test Entry"
        test_entry.productName = "Test Product"
        test_entry.artist = "Me"
        entries.append(test_entry)

        events = []
        for entry in tqdm(entries):
            entry:LLEntry = entry
            if not self.overlap(query_time_range, entry):
                continue

            if entry.imageFilePath is None or len(entry.imageFilePath) == 0:
                # media
                if len(entry.locations) > 0 and \
                    entry.locations[0] is not None:
                    media = {"url": self.create_map_link(entry.locations[0])}
                elif entry.artist != "":
                    media = {"url": "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"}
                elif entry.productName != "":
                    # TODO: search the product from amazon
                    media = {"url": """https://ws-eu.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=GB&ASIN=B07HS3Y5KH&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=AC_SL500"""}
                else:
                    # TODO: check other types of media
                    media = None

                # uid
                uid = entry.source + entry.startTime
                tags = entry.tags + [entry.source, entry.type]
                text, next_tags = self.entry_to_text(entry)

                slide = {
                    "start_date": self.convert_date(entry.startTime),
                    "end_date": self.convert_date(entry.endTime),
                    "text": self.create_text(entry.textDescription, text),
                    "media":  media,
                    "group": "LLEntry",
                    "unique_id": uid,
                    "tags": tags,
                    "next_tags": next_tags,
                    "parent": None,
                    "visible": False
                }
                events.append(slide)

        return events

    def overlap(self, time_range: Tuple[str], entry: LLEntry):
        """Check if two time ranges overlap
        """
        if time_range is None:
            return True

        r1 = (datetime.datetime.fromisoformat(time_range[0]).replace(tzinfo=pytz.utc).date(),
              datetime.datetime.fromisoformat(time_range[1]).replace(tzinfo=pytz.utc).date())
        r2 = (datetime.datetime.fromisoformat(entry.startTime).replace(tzinfo=pytz.utc).date(),
              datetime.datetime.fromisoformat(entry.endTime).replace(tzinfo=pytz.utc).date())

        latest_start = max(r1[0], r2[0])
        earliest_end = min(r1[1], r2[1])
        return earliest_end >= latest_start

    def create_timeline(self,
        query_time_range: Tuple[datetime.datetime]=None,
        add_LLEntries=False):
        """Generate JSON object for TimelineJS.
        """
        parent, children = self.create_summary_tree()

        # add day id for trip days
        for trip in self.trip_index.values():
            current_day = datetime.datetime.fromisoformat(trip.startTime)
            end_time = datetime.datetime.fromisoformat(trip.endTime)

            day_idx = 1
            while current_day <= end_time:
                # print(current_day, list(self.daily_index.keys())[:3])
                if current_day.date() in self.daily_index:
                    day = self.daily_index[current_day.date()]
                    if 'Day ' not in day.textDescription:
                        day.textDescription = f'Day {day_idx}: ' + day.textDescription
                day_idx += 1
                current_day += datetime.timedelta(days=1)

        result = {"events": []}
        print("Processing activities")
        for activity in tqdm(self.activity_index.values()):
            activity : LLEntrySummary = activity

            # skip summaries that are not in the query range
            if not self.overlap(query_time_range, activity):
               continue

            img_path = self.visualize_images(activity.image_paths)
            tags, next_tags = self.organize_tags(activity.objects,
                                                 self.get_city_country(activity.startGeoLocation))
            uid = self.get_uid(activity)
            slide = {"start_date": self.convert_date(activity.startTime),
                    "end_date": self.convert_date(activity.endTime),
                    "text": self.create_text(activity.textDescription, self.objects_to_text(activity.objects)),
                    "media": {"url": img_path, "thumbnail": img_path},
                    "group": "activity",
                    "unique_id": uid,
                    "tags": tags,
                    "next_tags": next_tags,
                    "background": {"url": activity.image_paths[0] + '.compressed.jpg'},
                    "parent": parent[uid],
                    "visible": False
                }
            # slide["tags"] += self.get_city_country(activity.startGeoLocation)
            # slide["tags"] += [activity.startGeoLocation.address.split(', ')[-1]]
            # if 'person' not in activity.objects:

            # hide an activity if it is the only one in a day
            date_str = datetime.datetime.fromisoformat(activity.startTime).date()
            if date_str in self.daily_index:
                num_activities = self.daily_index[date_str].stats["num_activities"]
            else:
                num_activities = 2

            if num_activities > 1:
                result['events'].append(slide)

        print("Processing days")
        for day in tqdm(self.daily_index.values()):
            day : LLEntrySummary = day
            # skip summaries that are not in the query range
            if not self.overlap(query_time_range, day):
               continue

            img_path = self.visualize_images(day.image_paths)
            tags, next_tags = self.organize_tags(day.objects,
                                                 self.get_city_country(day.startGeoLocation))
            uid = self.get_uid(day)
            slide = {
                "start_date": self.convert_date(day.startTime, 0),
                "end_date": self.convert_date(day.startTime, 24),
                "text": self.create_text(day.textDescription, self.objects_to_text(day.objects)),
                "media": {"url": img_path, "thumbnail": img_path},
                "group": "day",
                "unique_id": uid,
                "tags": tags,
                "next_tags": next_tags,
                "background": {"url": day.image_paths[0] + '.compressed.jpg'},
                "parent": parent[uid],
                "visible": True
            }
            # if 'person' not in day.objects:
            result['events'].append(slide)

        print("Processing trips")
        for trip in tqdm(self.trip_index.values()):
            trip : LLEntrySummary = trip
            if not self.overlap(query_time_range, trip):
               continue
            #     start_date_num = (itin_entry['start'] - trip['start_date']).days + 1
            #     end_date_num = (itin_entry['end'] - trip['start_date']).days + 1
            #     location_text = itin_entry['location'].replace(';', ', ')
            #     if start_date_num == end_date_num:
            #         text = f"Day {start_date_num}: {location_text}"
            #     else:
            #         text = f"Day {start_date_num} - Day {end_date_num}: {location_text}"
            tags, next_tags = self.organize_tags({},
                                                 self.get_city_country(trip.startGeoLocation))

            uid = self.get_uid(trip)
            slide = {
                "start_date": self.convert_date(trip.startTime, 0),
                "end_date": self.convert_date(trip.endTime, 24),
                "text": self.create_text(trip.textDescription, ""),
                "media": {"url": self.create_map_link(trip.startGeoLocation)},
                "group": "trip",
                "tags": tags,
                "next_tags": next_tags,
                "unique_id": uid,
                "parent": parent[uid],
                "visible": True
            }

            result['events'].append(slide)

        if add_LLEntries:
            result['events'] += self.load_and_display_LLEntries(query_time_range)

        return result

if __name__ == '__main__':
    if not os.path.exists("images/"):
        os.makedirs("images/")

    renderer = TimelineRenderer(path='.')
    json_obj = renderer.create_timeline(query_time_range=None, add_LLEntries=True)
    template = open('index.html.template').read()
    template = template.replace('"timeline object template"', json.dumps(json_obj))
    fout = open('index.html', 'w')
    fout.write(template)
    fout.close()

    # cards = renderer.create_cards()
    # template = open('search_result.html.template').read()
    # template = template.replace("<!-- card template -->", " ".join(cards))
    # fout = open('search_result.html', 'w')
    # fout.write(template)
    # fout.close()
