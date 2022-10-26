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

from typing import Dict, List
from tqdm import tqdm
from PIL import Image
from pillow_heif import register_heif_opener
from geopy import Location
import geopy.distance

from src.objects.LLEntry_obj import LLEntrySummary
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
        self.img_cnt = 0
        self.geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
        self.geo_cache = {}
        self.user_info = json.load(open("user_info.json"))
        self.home_address = self.geolocator.geocode(self.user_info["address"])

    def visualize_images(self, image_paths: List[str]):
        """visualize a list of images
        """
        path = "images/summary_%d.png" % (self.img_cnt)
        self.img_cnt += 1

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
        if 'address' not in location.raw or "city" not in location.raw['address']:
            coord = (location.latitude, location.longitude)
            if coord in self.geo_cache:
                location = self.geo_cache[coord]
            else:
                location = self.geolocator.reverse(coord)
                self.geo_cache[coord] = location

        def is_home(loc: Location, home: Location):
            """Check if a location is home (within 200km)."""
            return geopy.distance.geodesic((home.latitude, home.longitude),
               (loc.latitude, loc.longitude)).km <= 200.0
        
        res = []
        if is_home(location, self.home_address):
            res.append("Home")

        for attr in ["city", "state", "country"]:
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
        date = datetime.datetime.fromisoformat(date)
        if hour is not None:
            return {'year': date.year, 'month': date.month, 'day': date.day, 'hour': hour}
        else:
            return {'year': date.year, 'month': date.month, 'day': date.day}

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

    def create_timeline(self):
        """Generate JSON object for TimelineJS.
        """
        result = {"events": []}
        print("Processing activities")
        for activity in tqdm(self.activity_index.values()):
            activity : LLEntrySummary = activity
            img_path = self.visualize_images(activity.image_paths)
            tags, next_tags = self.organize_tags(activity.objects, 
                                                 self.get_city_country(activity.startGeoLocation))
            slide = {"start_date": self.convert_date(activity.startTime),
                    "end_date": self.convert_date(activity.endTime),
                    "text": self.create_text(activity.textDescription, self.objects_to_text(activity.objects)),
                    "media": {"url": img_path, "thumbnail": img_path},
                    "group": "activity",
                    "unique_id": f"activity_{activity.startTime}",
                    "tags": tags,
                    "next_tags": next_tags,
                    "background": {"url": activity.image_paths[0] + '.compressed.jpg'}
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

            img_path = self.visualize_images(day.image_paths)
            tags, next_tags = self.organize_tags(day.objects, 
                                                 self.get_city_country(day.startGeoLocation))
            slide = {
                "start_date": self.convert_date(day.startTime, 0),
                "end_date": self.convert_date(day.startTime, 24),
                "text": self.create_text(day.textDescription, self.objects_to_text(day.objects)),
                "media": {"url": img_path, "thumbnail": img_path},
                "group": "day",
                "unique_id": f"day_{day.startTime}",
                "tags": tags,
                "next_tags": next_tags,
                "background": {"url": day.image_paths[0] + '.compressed.jpg'}
            }
            # if 'person' not in day.objects:
            result['events'].append(slide)

        print("Processing trips")
        for trip in tqdm(self.trip_index.values()):
            trip : LLEntrySummary = trip
            # for itin_entry in trip['itinerary']:
            #     start_date_num = (itin_entry['start'] - trip['start_date']).days + 1
            #     end_date_num = (itin_entry['end'] - trip['start_date']).days + 1
            #     location_text = itin_entry['location'].replace(';', ', ')
            #     if start_date_num == end_date_num:
            #         text = f"Day {start_date_num}: {location_text}"
            #     else:
            #         text = f"Day {start_date_num} - Day {end_date_num}: {location_text}"
            tags, next_tags = self.organize_tags({}, 
                                                 self.get_city_country(trip.startGeoLocation))
            
            slide = {
                "start_date": self.convert_date(trip.startTime, None),
                "end_date": self.convert_date(trip.endTime, None),
                "text": self.create_text(trip.textDescription, ""),
                "media": {"url": self.create_map_link(trip.startGeoLocation)},
                "group": "trip",
                "tags": tags,
                "next_tags": next_tags
            }
            
            result['events'].append(slide)
        
        return result

if __name__ == '__main__':
    if not os.path.exists("images/"):
        os.makedirs("images/")

    renderer = TimelineRenderer(path='.')
    json_obj = renderer.create_timeline()
    template = open('index.html.template').read()
    template = template.replace('"timeline object template"', json.dumps(json_obj))
    fout = open('index.html', 'w')
    fout.write(template)
    fout.close()