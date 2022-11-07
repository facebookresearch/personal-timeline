import pickle
import os
import datetime
import pandas as pd
import spotipy

from glob import glob
from typing import Dict, List, Tuple
from pillow_heif import register_heif_opener
from geopy import Location
from collections import Counter
import geopy.distance
from spotipy.oauth2 import SpotifyClientCredentials

from src.objects.LLEntry_obj import LLEntrySummary, LLEntry
from src.persistence.personal_data_db import PersonalDataDBConnector
register_heif_opener()

map_api_key = os.getenv("GOOGLE_MAP_API")

class Summarizer:

    def __init__(self, path='.'):
        """Create summaries of LLEntry and LLEntrySummary
        """
        self.activity_index = pickle.load(open(os.path.join(path, 'activity_index.pkl'), 'rb'))
        self.daily_index = pickle.load(open(os.path.join(path, 'daily_index.pkl'), 'rb'))
        self.trip_index = pickle.load(open(os.path.join(path, 'trip_index.pkl'), 'rb'))
        # self.img_cache = {}
        # self.geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
        # self.geo_cache = {}
        # self.user_info = json.load(open("user_info.json"))
        # self.home_address = self.geolocator.geocode(self.user_info["address"])

        # load all non-photo LLEntries
        db = PersonalDataDBConnector()
        res = db.search_personal_data(select_cols="enriched_data",
                                      where_conditions={"enriched_data": "is not NULL"})
        self.all_entries:List[LLEntry] = []
        # add raw items
        for row in res.fetchall():
           entry:LLEntry = pickle.loads(row[0])
           self.all_entries.append(entry)

        # add summary items
        for item in self.activity_index.values():
            self.all_entries.append(item)
        for item in self.daily_index.values():
            self.all_entries.append(item)
        for item in self.trip_index.values():
            self.all_entries.append(item)


        # sort entries by timestamp
        self.all_entries.sort(key=lambda entry: datetime.datetime.fromisoformat(entry.startTime).timestamp())

        # load amazon raw records
        # scan all csv files
        self.product_image_index = {}
        dir_paths = ['personal-data/amazon-kindle', 'personal-data/amazon']
        for dir_path in dir_paths:
            all_csv_files = [file for path, subdir, files in os.walk(dir_path) \
                 for file in glob(os.path.join(path, "*.csv"))]
            for fn in all_csv_files:
                table = pd.read_csv(fn)
                if 'ASIN' in table and 'Title' in table:
                    for asin, product_name in zip(table['ASIN'], table['Title']):
                        self.product_image_index[product_name] = asin
                if 'ASIN' in table and 'Product Name' in table:
                    for asin, product_name in zip(table['ASIN'], table['Product Name']):
                        self.product_image_index[product_name] = asin

        # for spotify
        cid = os.environ['SPOTIFY_TOKEN'] 
        secret = os.environ['SPOTIFY_SECRET'] 
        client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


    def fetch_range(self, query_time_range: Tuple[str]) -> Tuple[int]:
        """Return a range of LLEntry that overlap with the query
        """
        start_ts = datetime.datetime.fromisoformat(query_time_range[0]).timestamp()
        end_ts = datetime.datetime.fromisoformat(query_time_range[1]).timestamp()
        res = []
        for ts in [start_ts, end_ts]:
            left = 0
            right = len(self.all_entries) - 1

            while right - left > 1:
                mid = (left + right) // 2
                mid_ts = datetime.datetime.fromisoformat(self.all_entries[mid].startTime).timestamp()
                if mid_ts < ts:
                    left = mid
                else:
                    right = mid
            
            res.append(right)
        return res

    def contains(self, time_range: Tuple[str], entry: LLEntry) -> bool:
        """Check if an entry falls into a time range
        """
        if time_range is None:
            return True

        def convert(date_str_list: List[str]):
            res = []
            for date_str in date_str_list:
                if date_str == '':
                    date_str = date_str_list[0]
                try:
                    ts = datetime.datetime.fromisoformat(date_str).timestamp()
                except:
                    ts = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z').timestamp()
                res.append(ts)

            return tuple(res)

        r1 = convert(list(time_range))
        r2 = convert([entry.startTime, entry.endTime])

        return r1[0] <= r2[0] <= r1[1] and r1[0] <= r2[1] <= r1[1]

    def summarize_exercises(self, entries: List[LLEntry]):
        """Summarize a list of exercise LLEntries
        """
        result = []
        if len(entries) <= 5:
            for entry in entries:
                result.append({"text": entry.type.split(':')[1], 
                               "detail": entry.textDescription})
        else:
            distance = Counter()
            calories = Counter()
            durations = Counter()
            for entry in entries:
                etype = entry.type.split(':')[1]
                distance[etype] += float(entry.distance)
                calories[etype] += float(entry.calories)
                durations[etype] += float(entry.duration)

            for key in distance:
                if distance[key] > 0:
                    mile_text = '%.1f miles, ' % distance[key]
                else:
                    mile_text = ""

                result.append({"text": key, 
                               "detail": "You exercised by %s for a total of %.1f minutes, %sand %.1f calories." \
                                % (key, durations[key], mile_text, calories[key])})
        return result


    def summarize_purchases(self, entries: List[LLEntry]):
        """Summarize a list of purchase LLEntries
        """
        result = []
        if len(entries) <= 3:
            for entry in entries:
                result.append({"text": entry.productName,
                               "detail": "%s at $%s" % (entry.productName, entry.productPrice)})
                if entry.productName in self.product_image_index:
                    result[-1]["media"] = f'https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US&ASIN={self.product_image_index[entry.productName]}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL250'
        else:
            total = 0.0
            total_items = 0.0
            most_expensive = Counter()
            most_frequent = Counter()
            for entry in entries:
                total += float(entry.productPrice) * float(entry.productQuantity)
                total_items += float(entry.productQuantity)
                most_frequent[entry.productName] += float(entry.productQuantity)
                most_expensive[entry.productName] = max(most_expensive[entry.productName], 
                                                        float(entry.productPrice))

            # total
            result.append({"text": "You spent a total of $%.1f" % total,
                           "detail": "You spent a total of $%.1f on %d items." % (total, total_items)})
            # the most expensive item
            result.append({"text": "The most expensive item ($%.1f)" % most_expensive.most_common(1)[0][1],
                           "detail": most_expensive.most_common(1)[0][0]})

            # the most frequent item
            result.append({"text": "The most frequent item (%.0f times)" % most_frequent.most_common(1)[0][1],
                           "detail": most_frequent.most_common(1)[0][0]})

        return result

    def get_img_path(self, img_path):
        """Convert an image path to server path.
        """
        if '.compressed.jpg' not in img_path:
            img_path += '.compressed.jpg'
        if 'static/' not in img_path:
            original = img_path
            img_path = 'static/' + os.path.split(img_path)[-1]
            if os.path.exists(original):
                os.system('cp "%s" static/' % (original))
        return img_path

    def summarize_persons(self, entries: List[LLEntry]):
        """Summarize a list of LLEntries with persons
        """
        persons = Counter()
        person_mp = {}
        result = []

        for entry in entries:
            for pp in entry.peopleInImage:
                pp = pp['name']
                persons[pp] += 1
                img_path = self.get_img_path(entry.imageFilePath)
                if pp not in person_mp:
                    person_mp[pp] = img_path
                result.append({"text": pp, "media": img_path})
        
        if len(result) >= 5:
            result = []
            for pp, frequency in persons.most_common(5):
                result.append({"text": f"{pp} for {frequency} times",
                               "media": person_mp[pp]})
        return result
        

    def summarize_places(self, entries: List[LLEntry]):
        """Summarize a list of LLEntries with locations
        """
        levels = [["town", "city", "county", "suburb"], 
                  ["state", "country"]]
        # TODO: detailed location name not in geopy location
        result = []
        for level in levels:
            cache = set([])
            result = []
            for entry in entries:
                for location in entry.locations:
                    if location is None:
                        continue
                    for attr in level:
                        if 'address' in location.raw and attr in location.raw['address']:
                            if location.raw['address'][attr] not in cache:
                                cache.add(location.raw['address'][attr])
                                result.append({"text": location.raw['address'][attr],
                                            "media": location})
                            break
            if len(result) <= 5:
                return result
                    
        return result

    def summarize_books(self, entries: List[LLEntry]):
        """Summarize a list of reading/book LLEntries
        """
        result = []
        for entry in entries:
            if entry.productName == 'Kindle Unlimited':
                continue
            author = entry.author
            if author == '':
                author = entry.productName
            author = entry.productName + f' ({author})'
            result.append({"text": author,
                           "detail": entry.productName})
            if entry.imageURL != "":
                result[-1]["media"] = entry.imageURL
            elif entry.productName in self.product_image_index:
                result[-1]["media"] = f'https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US&ASIN={self.product_image_index[entry.productName]}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL250'

        return result

    def summarize_streamings(self, entries: List[LLEntry]):
        """Summarize a list of streaming LLEntries
        """
        result = []
        summary = {}
        for entry in entries:
            if entry.artist not in summary:
                summary[entry.artist] = []
            
            if entry.track not in summary[entry.artist]:
                summary[entry.artist].append(entry.track)

        for artist, tracks in summary.items():
            result.append({"text": artist,
                           "detail": ', '.join(tracks)})
            
            # search spotify
            link = None
            try:
                res = self.spotify.search(q=f"artist: {artist} track:{tracks[0]}" , type="track", limit=5)
                if 'tracks' in res and 'items' in res['tracks']:
                    for item in res['tracks']['items']:
                        if 'external_urls' in item:
                            link = item['external_urls']['spotify']
                            break
            except:
                print("Spotify Exception: " + artist + " " + tracks)
            
            if link is not None:
                result[-1]['media'] = link

        return result


    def summarize(self, query_time_range: Tuple[str], brief=False):
        """Organize LLEntries of a certain time range into a summary.
        """
        start_idx, end_idx = self.fetch_range(query_time_range)
        sources = "GooglePhotos,GooglePhotos,GoogleTimeline,AppleHealth,Amazon,Spotify,Libby,AmazonKindle".split(',')
        types = "persons,places,places,exercises,items,streamings,books,books".split(',')
        summary = {}
        for key in types:
            summary[key] = []

        ents = []
        for entry in self.all_entries[start_idx - 1: end_idx + 1]:
            if not self.contains(query_time_range, entry):
                continue

            ents.append(entry)
            for source, stype in zip(sources, types):
                if entry.source == source:
                    summary[stype].append(entry)

        summary['exercises'] = self.summarize_exercises(summary['exercises'])
        summary['places'] = self.summarize_places(summary['places'])
        summary['persons'] = self.summarize_persons(summary['persons'])

        if not brief:
            summary['items'] = self.summarize_purchases(summary['items'])
            summary['streamings'] = self.summarize_streamings(summary['streamings'])
            summary['books'] = self.summarize_books(summary['books'])

        return summary


