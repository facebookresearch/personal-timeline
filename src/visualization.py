import pickle
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib
import json
import urllib.parse

from typing import Dict, List
from tqdm import tqdm
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()

matplotlib.use('Agg')

map_api_key = os.getenv("GOOGLE_MAP_API")

activity_index = pickle.load(open('activity_index.pkl', 'rb'))
daily_index = pickle.load(open('daily_index.pkl', 'rb'))
trip_index = pickle.load(open('trip_index.pkl', 'rb'))

img_cnt = 0

def visualize(image_paths: List[str]):
    """visualize a list of images
    """
    global img_cnt
    path = "images/summary_%d.png" % (img_cnt)
    img_cnt += 1

    if len(image_paths) == 1:
        return image_paths[0]

    if os.path.exists(path):
        return path

    plt.figure(figsize=(60,30))
    columns = 9
    for i, img_path in enumerate(image_paths[:9]):
        img = Image.open(img_path)
        plt.subplot(len(image_paths) // columns + 1, columns, i + 1)
        plt.imshow(img)
        plt.axis('off')

    plt.savefig(path, bbox_inches='tight')
    plt.close()
    return path

def create_map_link(location):
    """Generate a google map iframe.
    """
    location = location.replace(";", ' ')
    link = f'<iframe width="600" height="450" style="border:0" loading="lazy" allowfullscreen src="https://www.google.com/maps/embed/v1/place?key={map_api_key}&q={urllib.parse.quote(location)}"></iframe>'
    # print(link)
    return link

def convert_date(date: datetime.date, hour=None):
    """Reformating dates."""
    if hour is not None:
        return {'year': date.year, 'month': date.month, 'day': date.day, 'hour': hour}
    else:
        return {'year': date.year, 'month': date.month, 'day': date.day}

def create_text(headline, text):
    return {"headline": headline, "text": text}

def objects_to_text(object_dict: Dict):
    """Convert a object dictionary to text.
    """
    text = ""
    for tag in object_dict:
        text += f"<p>These are the {tag} that I saw: <ul><li>"
        itemized = []
        for item in object_dict[tag]:
            img_path = item["img_path"]
            name = item["name"]
            itemized.append(f'<a href="{img_path}">{name}</a>')
        text += ", ".join(itemized) + " </li> </ul>"
    return text

def visualize_activities(activity_index, daily_index, trip_index):
    """Generate JSON object for TimelineJS.
    """
    result = {"events": []}
    print("Processing activities")
    for activity in tqdm(activity_index.values()):
        img_path = visualize(activity['photo_summary'])
        slide = {"start_date": convert_date(activity['date'], activity['start_hour']),
                 "end_date": convert_date(activity['date'], activity['end_hour']),
                 "text": create_text(activity['summary'], objects_to_text(activity["objects"])),
                 "media": 
                   {
                     "url": img_path
                   },
                 "group": "activity",
                 "unique_id": f"activity_{activity['date']}_{activity['start_hour']}"
                }
        result['events'].append(slide)
    
    print("Processing days")
    for day in tqdm(daily_index.values()):
        img_path = visualize(day['photo_summary'])
        slide = {
            "start_date": convert_date(day['date'], 0),
            "end_date": convert_date(day['date'], 24),
            "text": create_text(day['summary'], objects_to_text(day["objects"])),
            "media": {"url": img_path},
            "group": "day",
            "unique_id": f"day_{day['date']}"
        }
        result['events'].append(slide)

    print("Processing trips")
    for trip in tqdm(trip_index.values()):        
        for itin_entry in trip['itinerary']:
            start_date_num = (itin_entry['start'] - trip['start_date']).days + 1
            end_date_num = (itin_entry['end'] - trip['start_date']).days + 1
            location_text = itin_entry['location'].replace(';', ', ')
            if start_date_num == end_date_num:
                text = f"Day {start_date_num}: {location_text}"
            else:
                text = f"Day {start_date_num} - Day {end_date_num}: {location_text}"

            slide = {
                "start_date": convert_date(itin_entry['start'], None),
                "end_date": convert_date(itin_entry['end'], None),
                "text": create_text(trip['summary'], text),
                "media": {"url": create_map_link(itin_entry['location'])},
                "group": "trip"
            }
            result['events'].append(slide)
    
    return result

if __name__ == '__main__':
    if not os.path.exists("images/"):
        os.makedirs("images/")

    json_obj = visualize_activities(activity_index, daily_index, trip_index)
    template = open('index.html.template').read()
    template = template.replace('"timeline object template"', json.dumps(json_obj))
    fout = open('index.html', 'w')
    fout.write(template)
    fout.close()