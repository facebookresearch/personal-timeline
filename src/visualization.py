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

from typing import Dict, List, Tuple, Union
from tqdm import tqdm
from PIL import Image
from pillow_heif import register_heif_opener
from geopy import Location
import geopy.distance

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
        self.user_info = json.load(open("user_info.json"))
        self.home_address = self.geolocator.geocode(self.user_info["address"])

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
                if not os.path.exists(os.path.join('static/', tail)):
                    os.system('cp "%s" static/' % (img_path))

                # itemized.append(f'<a href="{img_path}">{name}</a>')
                itemized.append(f'''<div class="tooltip"><a href="static/{tail}">{name}</a>
                               <span class="tooltiptext">
                               <img src="static/{tail}" alt="image" height="200" /></span>
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

        if len(summary.image_paths) > 0:
            img_path = summary.image_paths[0] + '.compressed.jpg'
            if summary.startTime == summary.endTime:
                summary_time = summary.startTime
            else:
                summary_time = f"{summary.startTime} - {summary.endTime}"

            new_img_path = 'static/' + os.path.split(img_path)[-1]
            if not os.path.exists(new_img_path):
                os.system('cp "%s" static/' % (img_path))
        else:
            new_img_path = ""

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
            res += f"""<a href="'''{img_path}">{name}</a>"""
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
        keys = "persons,exercises,items,places,streamings,books".split(",")
        verbs = ["met", "did", "purchased", "have been to", "listened to", "read"]

        for key, verb in zip(keys, verbs):
            if key not in summary:
                continue
            value = summary[key]
            if len(value) == 0:
                continue
            text += f"<p>These are the {key} that I {verb}:</p> <div class='row'>"

            for v in value:
                obj = self.create_hover_object(v)
                text += f"""<div class="column">
                            <div class="card">{obj}</div></div>
                """

            text += '</div><br>'

        return text


    # def load_and_display_LLEntries(self, query_time_range: Tuple[str]=None):
    #     """Visualize non-image LLEntries
    #     """

    #     # for testing
    #     # test_entry = LLEntry("testing", "2018-08-30T00:05:23", "testing")
    #     # test_entry.textDescription = "Test Entry"
    #     # test_entry.productName = "Test Product"
    #     # test_entry.artist = "Me"
    #     # entries.append(test_entry)

    #     events = []
    #     for entry in tqdm(self.non_photo_entries):
    #         entry:LLEntry = entry
    #         if not self.overlap(query_time_range, entry):
    #             continue

    #         if entry.imageFilePath is None or len(entry.imageFilePath) == 0:
    #             # media
    #             if len(entry.locations) > 0 and \
    #                 entry.locations[0] is not None:
    #                 media = {"url": self.create_map_link(entry.locations[0])}
    #             elif entry.artist != "":
    #                 media = {"url": "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"}
    #             elif entry.productName != "":
    #                 # TODO: search the product from amazon
    #                 media = {"url": """https://ws-eu.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=GB&ASIN=B07HS3Y5KH&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=AC_SL500"""}
    #             else:
    #                 # TODO: check other types of media
    #                 media = None

    #             # uid
    #             uid = entry.source + entry.startTime
    #             tags = entry.tags + [entry.source, entry.type]
    #             text, next_tags = self.entry_to_text(entry)

    #             # TODO: figure out the data formating issue
    #             if entry.endTime == '':
    #                 entry.endTime = entry.startTime

    #             slide = {
    #                 "start_date": self.convert_date(entry.startTime),
    #                 "end_date": self.convert_date(entry.endTime),
    #                 "text": self.create_text(entry.textDescription, text),
    #                 "media":  media,
    #                 "group": "LLEntry",
    #                 "unique_id": uid,
    #                 "tags": tags,
    #                 "next_tags": next_tags,
    #                 "parent": None,
    #                 "visible": False
    #             }
    #             events.append(slide)

    #     return events

    def overlap(self, time_range: Tuple[str], entry: LLEntry):
        """Check if two time ranges overlap
        """
        if time_range is None:
            return True

        def convert(date_str_list: List[str]):
            res = []
            for date_str in date_str_list:
                if date_str == '':
                    date_str = date_str_list[0]
                try:
                    dt = datetime.datetime.fromisoformat(date_str).replace(tzinfo=pytz.utc)
                except:
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
                res.append(dt.date())

            return tuple(res)

        r1 = convert(list(time_range))
        r2 = convert([entry.startTime, entry.endTime])

        latest_start = max(r1[0], r2[0])
        earliest_end = min(r1[1], r2[1])
        return earliest_end >= latest_start

    def create_timeline(self):
        """Generate JSON object for TimelineJS.
        """
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

        # result = {"events": []}
        # print("Processing activities")
        # for activity in tqdm(self.activity_index.values()):
        #     activity : LLEntrySummary = activity

        #     # skip summaries that are not in the query range
        #     if not self.overlap(query_time_range, activity):
        #        continue

        #     img_path = self.visualize_images(activity.image_paths) # (activity.image_paths)
        #     tags, next_tags = self.organize_tags(activity.objects,
        #                                          self.get_city_country(activity.startGeoLocation))
        #     uid = self.get_uid(activity)
        #     slide = {"start_date": self.convert_date(activity.startTime),
        #             "end_date": self.convert_date(activity.endTime),
        #             "text": self.create_text(activity.textDescription, self.objects_to_text(activity.objects)),
        #             "media": {"url": img_path, "thumbnail": img_path},
        #             "group": "activity",
        #             "unique_id": uid,
        #             "tags": tags,
        #             "next_tags": next_tags,
        #             "background": {"url": activity.image_paths[0] + '.compressed.jpg'},
        #         }
        #     # slide["tags"] += self.get_city_country(activity.startGeoLocation)
        #     # slide["tags"] += [activity.startGeoLocation.address.split(', ')[-1]]
        #     # if 'person' not in activity.objects:

        #     # hide an activity if it is the only one in a day
        #     date_str = datetime.datetime.fromisoformat(activity.startTime).date()
        #     if date_str in self.daily_index:
        #         num_activities = self.daily_index[date_str].stats["num_activities"]
        #     else:
        #         num_activities = 2

        #     if num_activities > 1:
        #         result['events'].append(slide)

        # print("Processing days")
        # for day in tqdm(self.daily_index.values()):
        #     day : LLEntrySummary = day
        #     # skip summaries that are not in the query range
        #     if not self.overlap(query_time_range, day):
        #        continue

        #     img_path = self.visualize_images(day.image_paths)
        #     tags, next_tags = self.organize_tags(day.objects,
        #                                          self.get_city_country(day.startGeoLocation))
        #     uid = self.get_uid(day)
        #     slide = {
        #         "start_date": self.convert_date(day.startTime, 0),
        #         "end_date": self.convert_date(day.startTime, 24),
        #         "text": self.create_text(day.textDescription, self.objects_to_text(day.objects)),
        #         "media": {"url": img_path, "thumbnail": img_path},
        #         "group": "day",
        #         "unique_id": uid,
        #         "tags": tags,
        #         "next_tags": next_tags,
        #         "background": {"url": day.image_paths[0] + '.compressed.jpg'},
        #     }

        #     # add summary of non-photo LLEntries
        #     # slide["text"]["text"] += self.organize_LLEntries(())
        #     if add_LLEntries:
        #         startTime = self.convert_date(day.startTime, 0, get_str=True)
        #         endTime = self.convert_date(day.endTime, 24, get_str=True)
        #         slide['text']['text'] += self.organize_LLEntries((startTime, endTime))

        #     result['events'].append(slide)
        result = {'events': []}

        print("Processing years")
        for year in range(2012, 2023):
            startTime = '%s-01-01' % year
            endTime = '%s-01-01' % (year+1)
            slide = {
                "start_date": self.convert_date(startTime, 0),
                "end_date": self.convert_date(endTime, 0),
                "text": self.create_text("The year of %s" % year, self.organize_LLEntries((startTime, endTime))),
                "group": "year",
                "unique_id": "year_%d" % year}
            result['events'].append(slide)

        # print("Processing trips")
        for trip in tqdm(self.trip_index.values()):
            trip : LLEntrySummary = trip
            tags, next_tags = self.organize_tags({},
                                                 self.get_city_country(trip.startGeoLocation))

            start_date = datetime.datetime.fromisoformat(trip.startTime)
            end_date = datetime.datetime.fromisoformat(trip.endTime) + datetime.timedelta(days=1)

            uid = 'trip_%d_%d_%d' % (start_date.year, start_date.month, start_date.day)
            slide = {
                "start_date": self.convert_date(trip.startTime, 0),
                "end_date": self.convert_date(trip.endTime, 24),
                "text": self.create_text(trip.textDescription, ""),
                "media": {"url": self.create_map_link(trip.startGeoLocation)},
                "group": "trip",
                "tags": tags,
                "next_tags": next_tags,
                "unique_id": uid
            }
            slide['text']['text'] += self.organize_LLEntries((start_date.isoformat(), 
                                                              end_date.isoformat()))
            result['events'].append(slide)

        return result

    def add_summary_to_slide(self, slide: Dict, summary: LLEntrySummary):
        """Modify a slide by adding a LLEntrySummary object
        """
        if summary is None:
            return slide

        # modify text
        original_text = slide["text"]['text']
        slide["text"] = self.create_text(summary.textDescription, self.objects_to_text(summary.objects))
        slide["text"]['text'] += original_text

        # add tags
        if summary.type == 'trip':
            slide["tags"], slide["next_tags"] = self.organize_tags({},
                                                self.get_city_country(summary.startGeoLocation))
        else:
            slide["tags"], slide["next_tags"] = self.organize_tags(summary.objects,
                                                self.get_city_country(summary.startGeoLocation))
        
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
                    "end_date": self.convert_date(endTime, 0),
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
                    print("found")
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

if __name__ == '__main__':
    if not os.path.exists("static/"):
        os.makedirs("static/")

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
