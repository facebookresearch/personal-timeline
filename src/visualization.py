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
import calendar
import pandas as pd
import random

from typing import Dict, List, Tuple, Union
from tqdm import tqdm
from PIL import Image
from pillow_heif import register_heif_opener
from geopy import Location

from src.objects.LLEntry_obj import LLEntrySummary, LLEntry
from src.persistence.personal_data_db import PersonalDataDBConnector
from src.summarizer import Summarizer
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
        self.timeline_cached = None

        # for summarization
        self.summarizer = Summarizer()

        # load amazon raw records
        self.product_image_index = {}
        if os.path.exists('personal-data/amazon/Digital-Items.csv'):
            table = pd.read_csv('personal-data/amazon/Digital-Items.csv')
            for asin, product_name in zip(table['ASIN'], table['Title']):
                self.product_image_index[product_name] = asin
        
        # reindex activity by start datetime
        new_activity_index = {}
        for activity in self.activity_index.values():
            start_time = datetime.datetime.fromisoformat(activity.startTime)
            new_activity_index[(start_time.year, start_time.month, 
                                start_time.day, start_time.hour)] = activity
        
        self.activity_index = new_activity_index

        # slide cache
        self.slide_cache = {}


    def visualize_images(self, image_paths: List[str]):
        """visualize a list of images
        """
        signature = '_'.join([os.path.split(path)[1] for path in image_paths])
        if signature not in self.img_cache:
            path = "static/summary_%s.png" % (signature)
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
        """Get city, state, and country from location
        """
        # TODO: dig deeper to find a better fix
        if location is None:
            return []

        if 'address' not in location.raw or "country" not in location.raw['address']:
            coord = (location.latitude, location.longitude)
            if coord in self.geo_cache:
                location = self.geo_cache[coord]
            else:
                location = self.geolocator.reverse(coord, language='en')
                self.geo_cache[coord] = location

        res = []

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


    def create_map_link(self, location: Location, exact=True):
        """Generate a google map iframe.
        """
        if exact:
            query = urllib.parse.quote("%f,%f" % (location.latitude, location.longitude))
        else:
            location_list = self.get_city_country(location)
            location = " ".join(location_list)
            query = urllib.parse.quote(location)
        link = f'<iframe width="600" height="450" style="border:0" loading="lazy" allowfullscreen src="https://www.google.com/maps/embed/v1/place?key={map_api_key}&q={query}"></iframe>'
        # print(link)
        return link

    def create_spotify_link(self, link: str):
        """Create an iframe for spotify.
        """
        if '/embed/' not in link:
            link = link.replace('/track/', '/embed/track/')
        iframe = f"""<iframe style="border-radius:12px" src="{link}" 
        width="100%" height="380" frameBorder="0" allowfullscreen="" allow="autoplay; 
        clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
        """
        return iframe

    def convert_date(self, date: Union[str, datetime.datetime], hour=None, get_str=False):
        """Reformating dates."""

        if isinstance(date, str):
            try:
                dt = datetime.datetime.fromisoformat(date)
            except:
                dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z')
        else:
            dt = date

        if hour == 24:
            dt += datetime.timedelta(days=1)
            hour = 0
        
        if get_str:
            return dt.date().isoformat()

        if hour is not None:
            return {'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': hour}
        else:
            return {'year': dt.year, 'month': dt.month, 'day': dt.day, 'hour': dt.hour}

    def create_text(self, headline, text):
        return {"headline": headline, "text": text}

    def objects_to_text(self, object_dict: Dict, max_len=30):
        """Convert a object dictionary to text.
        """
        text = ""
        others = []
        other_tags = 'person,people,product,building,vehicle,document'.split(',')
        for tag in object_dict:
            if 'person' in tag or 'people' in tag:
                continue
            if any([ot in tag for ot in other_tags]):
                others += object_dict[tag]
        
        object_dict["others"] = others

        for tag in object_dict:
            if any([ot in tag for ot in other_tags]):
                continue
            text += f"<p>{tag.capitalize()}: </p> <div class='row'>"
            text += """
          <div class="timeline-steps aos-init aos-animate" data-aos="fade-up">
            """
            
            object_list = object_dict[tag]
            if len(object_list) > max_len:
                object_list = [object_list[i] for i in random.sample(range(len(object_list)), k=max_len)]

            for item in object_list:
                img_path = item["img_path"] + '.compressed.jpg'
                name = item["name"]
                _, tail = os.path.split(img_path)
                new_path = os.path.join('static/', tail)
                if not os.path.exists(new_path):
                    os.system('cp "%s" static/' % (img_path))

                obj = self.create_hover_object({"text": name, "detail": name, "media": new_path})
                time_str = item['datetime'].strftime('%b %d, %Y %H:%M')

                text += """
                         <div class="timeline-step">
                         <div class="timeline-content" data-toggle="popover" data-trigger="hover" data-placement="top" title="" data-content="And here's some amazing content. It's very engaging. Right?" data-original-title="2003">
                         <div class="inner-circle"></div>
                      """
                text += f'<p class="h6 mt-3 mb-1">{time_str}</p>'
                text += f'<div class="card">{obj}</div></div></div>'

                # text += f"""<div class="column">
                #             <div class="card">{obj}</div></div>"""
            text += "</div></div><br>"

        del object_dict["others"]

        return text


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

    def create_hover_object(self, object: Dict):
        """Create a hovering object
        """
        name = object["text"]
        if "detail" in object:
            text = object["detail"]
        else:
            text = ""

        img_path, spotify_path, location = None, None, None

        if "media" in object:
            if isinstance(object["media"], str):
                if 'spotify' in object["media"]:
                    spotify_path = object["media"]
                else:
                    img_path = object["media"]
            else:
                location = object["media"]

        res = '<div class="tooltip">'
        if len(name) >= 37:
            name = name[:37] + '...'
        if img_path is not None:
            res += f"""<a href="{img_path}">{name}</a>"""
        else:
            res += name

        if img_path is not None:
            res += '<span class="tooltipimage">'
            res += f"""<img src="{img_path}" alt="image" height="200" />"""
        elif spotify_path is not None:
            res += '<span class="tooltipmap">' + self.create_spotify_link(spotify_path)
        elif location is not None:
            map_link = self.create_map_link(location, exact=True)
            res += '<span class="tooltipmap">' + map_link
        elif text is not None:
            res += '<span class="tooltiptext">' + text
        res += '</span></div>'
        return res

    def organize_LLEntries(self, query_time_range: Tuple[datetime.datetime]):
        """Organize LLEntries of a certain time range into a summary.
        """
        summary = self.summarizer.summarize(query_time_range)

        text = ""
        keys = "exercises,items,common places,places,streamings,books".split(",")
        # verbs = ["did", "purchased", "have been to", "listened to", "read"]
        icon_map = {"running": "fa-solid fa-person-running",
                    "walking": "fa-solid fa-person-walking", 
                    "weight lifting": "fa-solid fa-dumbbell",
                    "yoga": "fa-solid fa-seedling",
                    "elliptical": "fa-regular fa-circle-ellipsis",
                    "rowing": "fa-solid fa-person-drowning"}

        for key in keys:
            if key not in summary:
                continue
            value = summary[key]
            if len(value) == 0:
                continue

            # only special case
            if key == 'items':
                key = 'Shopping'

            text += f"<p>{key.capitalize()}:</p> <div class='row'>"

            if key == 'places' and len(value) > 1:
                text += """<div class="timeline-steps aos-init aos-animate" data-aos="fade-up">"""

                for v in value:
                    obj = self.create_hover_object(v)
                    try:
                        time_str = v['datetime'].strftime('%b %d, %Y %H:%M')
                    except:
                        time_str = ""

                    text += """
                            <div class="timeline-step">
                            <div class="timeline-content" data-toggle="popover" data-trigger="hover" data-placement="top" title="" data-content="And here's some amazing content. It's very engaging. Right?" data-original-title="2003">
                            <div class="inner-circle"></div>
                        """
                    text += f'<p class="h6 mt-3 mb-1">{time_str}</p>'
                    text += f'<div class="card">{obj}</div></div></div>'

                text += "</div></div><br>"
            else:
                for v in value:
                    obj = self.create_hover_object(v)
                    if v["text"] in ["running", "elliptical", "walking", "yoga", "weight lifting", "rowing"]:
                        obj = f"""<i class="{icon_map[v['text']]}"></i> """ + obj

                    text += f"""<div class="column">
                                <div class="card">{obj}</div></div>
                    """

            text += '</div><br>'

        return text


    def create_timeline(self):
        """Generate JSON object for TimelineJS.
        """
        if self.timeline_cached is not None:
            return self.timeline_cached

        # add day id for trip days
        for trip in self.trip_index.values():
            current_day = datetime.datetime.fromisoformat(trip.startTime)
            end_time = datetime.datetime.fromisoformat(trip.endTime)

            try:
                trip_loc_str = trip.textDescription.split("trip to ")[1].split(",")[0]
            except:
                continue

            day_idx = 1
            while current_day <= end_time:
                # print(current_day, list(self.daily_index.keys())[:3])
                if current_day.date() in self.daily_index:
                    day = self.daily_index[current_day.date()]
                    if 'On the trip to' not in day.textDescription:
                        day.textDescription = day.textDescription + ": on the trip to " + trip_loc_str
                    
                    for key in day.objects:
                        if key not in trip.objects:
                            trip.objects[key] = []
                        for v in day.objects[key]:
                            trip.objects[key].append(v)
                day_idx += 1
                current_day += datetime.timedelta(days=1)

        result = {'events': []}

        print("Processing years")
        for year in tqdm(range(2012, 2023)):
            startTime = '%s-01-01' % year
            endTime = '%s-01-01' % (year+1)
            slide = {
                "start_date": self.convert_date(startTime, 0),
                "end_date": self.convert_date(endTime, 0),
                "text": self.create_text("The year %s" % year, self.organize_LLEntries((startTime, endTime))),
                "group": "year",
                "unique_id": "year_%d" % year}
            result['events'].append(slide)

        # print("Processing trips")
        for trip in tqdm(self.trip_index.values()):
            trip : LLEntrySummary = trip
            start_date = datetime.datetime.fromisoformat(trip.startTime)
            end_date = datetime.datetime.fromisoformat(trip.endTime) + datetime.timedelta(days=1)

            uid = 'trip_%d_%d_%d' % (start_date.year, start_date.month, start_date.day)
            slide = {
                "start_date": self.convert_date(trip.startTime, 0),
                "end_date": self.convert_date(trip.endTime, 24),
                "text": self.create_text(trip.textDescription, self.objects_to_text(trip.objects)),
                "media": {"url": self.create_map_link(trip.startGeoLocation)},
                "group": "trip",
                "unique_id": uid
            }
            slide['text']['text'] = self.organize_LLEntries((start_date.isoformat(), 
                                                              end_date.isoformat())) + slide['text']['text']
            result['events'].append(slide)

            # caching for retrieval
            self.slide_cache[uid] = slide

        self.timeline_cached = result
        return result

    # def get_trip_location(self, summary: LLEntrySummary):
    #     """Get the main location of a trip.
    #     """
    #     for location in summary.locations():
    #         pass


    def add_summary_to_slide(self, slide: Dict, summary: LLEntrySummary):
        """Modify a slide by adding a LLEntrySummary object
        """
        if summary is None:
            return slide

        # modify text
        original_text = slide["text"]['text']
        slide["text"] = self.create_text(summary.textDescription, self.objects_to_text(summary.objects))
        slide["text"]['text'] = original_text + slide["text"]['text']

        # add media
        if summary.type == 'trip':
            slide["media"] = {"url": self.create_map_link(summary.startGeoLocation)}
        else:
            img_path = self.visualize_images(summary.image_paths)
            slide["media"] = {"url": img_path, "thumbnail": img_path}
            slide["background"] = {"url": self.summarizer.get_img_path(summary.image_paths[0])}

        return slide


    def split_slide(self, unique_id: str) -> List[Dict]:
        """Return children slides given a unique slide/event ID.
        """
        tags = unique_id.split('_')
        result = []
        if tags[0] == 'year':
            # split year into months
            year = int(tags[1])
            for month in range(1, 13):
                startTime = datetime.date(year, month, 1)
                endTime = datetime.date(year, month, calendar.monthrange(year, month)[1]) + datetime.timedelta(days=1)
                slide = {
                    "start_date": self.convert_date(startTime, 0),
                    "end_date": self.convert_date(endTime, 0),
                    "text": self.create_text(startTime.strftime("%B %Y"), 
                            self.organize_LLEntries((startTime.isoformat(), endTime.isoformat()))),
                    "group": "month",
                    "unique_id": "month_%d_%d" % (year, month)
                }
                if slide["text"]["text"].strip() != "":
                    result.append(slide)
        elif tags[0] == 'month':
            # split month into weeks
            year, month = int(tags[1]), int(tags[2])
            last_day = calendar.monthrange(year, month)[1]
            for day in range(1, last_day, 7):
                startTime = datetime.date(year, month, day)
                endTime = startTime + datetime.timedelta(days=7)
                # overflow
                if endTime.day + 7 > last_day:
                    endTime = datetime.date(year, month, last_day)
                slide = {
                    "start_date": self.convert_date(startTime, 0),
                    "end_date": self.convert_date(endTime, 0),
                    "text": self.create_text("The week of %d/%d/%d-%d" % (year, month, day, endTime.day),
                            self.organize_LLEntries((startTime.isoformat(), endTime.isoformat()))),
                    "group": "week",
                    "unique_id": "week_%d_%d_%d" % (year, month, day)
                }
                if slide["text"]["text"].strip() != "":
                    result.append(slide)
                if endTime.day == last_day:
                    break
        elif tags[0] == 'week' or tags[0] == 'trip':
            # split week into days
            year, month, start_day = int(tags[1]), int(tags[2]), int(tags[3])
            first_day_date = datetime.datetime(year, month, start_day)

            if tags[0] == 'week':
                last_day = calendar.monthrange(year, month)[1]
                end_day = start_day + 7
                if end_day + 7 > last_day:
                    end_day = last_day
                last_day_date = datetime.datetime(year, month, end_day)
            else:
                # get last day + 1 of the trip
                trip = self.trip_index[first_day_date.date()]
                last_day_date = datetime.datetime.fromisoformat(trip.endTime)
                
            day = first_day_date

            while day <= last_day_date:
                startTime = day
                endTime = startTime + datetime.timedelta(days=1)
                slide = {
                    "start_date": self.convert_date(startTime, 0),
                    # "end_date": self.convert_date(endTime, 0),
                    "text": self.create_text(startTime.strftime("%B %d, %Y"),
                            self.organize_LLEntries((startTime.isoformat(), endTime.isoformat()))),
                    "group": "day",
                    "unique_id": "day_%d_%d_%d" % (startTime.year, startTime.month, startTime.day)
                }
                # add summary if indexed
                if day.date() in self.daily_index:
                    self.add_summary_to_slide(slide, self.daily_index[day.date()])
                if slide["text"]["text"].strip() != "":
                    result.append(slide)
                day += datetime.timedelta(days=1)
        elif tags[0] == 'day':
            # split day into hours and activities
            year, month, day = int(tags[1]), int(tags[2]), int(tags[3])
            startTime = datetime.datetime(year, month, day, 0)
            while startTime <= datetime.datetime(year, month, day, 0) + datetime.timedelta(days=1):
                activity = None
                endTime = startTime + datetime.timedelta(hours=1)
                key = (startTime.year, startTime.month, startTime.day, startTime.hour)
                if key in self.activity_index:
                    activity:LLEntrySummary = self.activity_index[key]
                    while endTime < datetime.datetime.fromisoformat(activity.endTime):
                        endTime += datetime.timedelta(hours=1)
                slide = {
                    "start_date": self.convert_date(startTime),
                    "end_date": self.convert_date(endTime),
                    "text": self.create_text("The hour of %d:00 to %d:00, %s" % (startTime.hour, endTime.hour, startTime.strftime("%B %d, %Y")),
                            self.organize_LLEntries((startTime.isoformat(), endTime.isoformat()))),
                    "group": "day",
                    "unique_id": "hour_%d_%d_%d_%d" % (startTime.year, startTime.month, startTime.day, startTime.hour)
                }
                if activity is not None:
                    self.add_summary_to_slide(slide, activity)
                if slide["text"]["text"].strip() != "":
                    result.append(slide)
                
                startTime = endTime

        return result

    def get_next_prev(self, unique_id:str) -> List[Dict]:
        """Return the next and previous slide
        """
        tag = unique_id.split('_')[0]
        result = []
        for delta in [1, -1]:
            # TODO: also support months and weeks
            if tag == 'day':
                _, year, month, day = unique_id.split('_')
                delta = datetime.timedelta(days=delta)
                current_date = datetime.datetime(int(year), int(month), int(day))
                dt = current_date + delta
                new_unique_id = '%s_%d_%d_%d' % (tag, dt.year, dt.month, dt.day)
                result.append(self.uid_to_slide(new_unique_id))
        return result


    def uid_to_slide(self, unique_id: str) -> Dict:
        """Retrieve a slide given a unique ID of trip or day.
        """
        if unique_id in self.slide_cache:
            return self.slide_cache[unique_id]

        tag = unique_id.split('_')[0]

        if tag == 'year':
            # for year
            _, year = unique_id.split('_')
            year = int(year)
            startTime = '%d-01-01' % year
            endTime = '%d-01-01' % (year+1)
            slide = {
                "start_date": self.convert_date(startTime, 0),
                "end_date": self.convert_date(endTime, 0),
                "text": self.create_text("The year %s" % year, self.organize_LLEntries((startTime, endTime))),
                "group": "year",
                "unique_id": "year_%d" % year}
        elif tag == 'month':
            _, year, month = unique_id.split('_')
            year, month = int(year), int(month)
            startTime = datetime.date(year, month, 1)
            endTime = datetime.date(year, month, calendar.monthrange(year, month)[1]) + datetime.timedelta(days=1)
            slide = {
                "start_date": self.convert_date(startTime, 0),
                "end_date": self.convert_date(endTime, 0),
                "text": self.create_text(startTime.strftime("%B %Y"), 
                        self.organize_LLEntries((startTime.isoformat(), endTime.isoformat()))),
                "group": "month",
                "unique_id": "month_%d_%d" % (year, month)
            }
        else:
            # for day
            _, year, month, day = unique_id.split('_')
            start_date = datetime.datetime(int(year), int(month), int(day))
            end_date = start_date + datetime.timedelta(days=1)

            slide = {
                "start_date": self.convert_date(start_date.isoformat(), 0),
                # "end_date": self.convert_date(end_date.isoformat(), 0),
                "text": self.create_text(start_date.strftime("%B %d, %Y"),
                        self.organize_LLEntries((start_date.isoformat(), end_date.isoformat()))),
                "group": "day",
                "unique_id": "day_%s_%s_%s" % (year, month, day)
            }
            # add summary if indexed
            if start_date.date() in self.daily_index:
                self.add_summary_to_slide(slide, self.daily_index[start_date.date()])
        
        self.slide_cache[unique_id] = slide
        return slide

if __name__ == '__main__':
    if not os.path.exists("static/"):
        os.makedirs("static/")

    renderer = TimelineRenderer(path='.')
    json_obj = renderer.create_timeline()
    # template = open('index.html.template').read()
    # template = template.replace('"timeline object template"', json.dumps(json_obj))
    # fout = open('index.html', 'w')
    # fout.write(template)
    # fout.close()

    # cards = renderer.create_cards()
    # template = open('search_result.html.template').read()
    # template = template.replace("<!-- card template -->", " ".join(cards))
    # fout = open('search_result.html', 'w')
    # fout.write(template)
    # fout.close()
