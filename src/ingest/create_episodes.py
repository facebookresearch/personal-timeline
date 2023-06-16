# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import json
import pandas as pd
import os
import spotipy

from typing import List
from glob import glob
from spotipy.oauth2 import SpotifyClientCredentials


class EpisodeCreator:

    def __init__(self, app_path='personal-data/app_data/'):
        self.app_path = app_path
        self.table = json.load(open(os.path.join(app_path, 'raw_data.db.json')))

        # index for amazon images
        self.product_image_index = {}

    def create_all_episodes(self):
        """Create episodes for all episode types.
        """
        table_names = 'books,exercise,places,purchase,streaming'.split(',')
        all_episodes = []
        for table_name in table_names:
            print("Processing %s" % table_name)
            func_name = 'create_%s_table' % table_name
            # func = globals()[func_name]
            func = getattr(self, func_name)
            episodes = func(self.table)

            # no episodes from the data source
            if len(episodes) == 0:
                continue

            # csv
            csv_path = os.path.join(self.app_path, '%s.csv' % table_name)
            table_csv = pd.read_csv(csv_path)
            table_csv['id'] = list(['%s_%d' % (table_name, i) for i in range(len(episodes))])
            table_csv.to_csv(csv_path, index=False)

            # json
            json_path = os.path.join(self.app_path, '%s.json' % table_name)
            table_json = json.load(open(json_path))
            for i, row in enumerate(table_json):
                row['id'] = '%s_%d' % (table_name, i)
                episodes[i]['id'] = '%s_%d' % (table_name, i)
            json.dump(table_json, open(json_path, 'w'))

            all_episodes += episodes

        # csv, json, episodes
        output_path = os.path.join(self.app_path, 'episodes.csv')
        pd.DataFrame(all_episodes).to_csv(output_path, index=False)

    
    def create_books_index(self):
        """Processing for amazon products.
        """
        # TODO: check path
        # '../../../personal-timeline-demo/personal-data/amazon-bak/'
        dir_paths = [self.app_path]
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


    def create_books_table(self, table: List):
        """Create a list of books/reading episodes.
        """
        output = []
        episodes = []
        for rec in table:
            if rec['source'] == 'Libby':
                output.append({'time': rec['startTime'],
                            'book_name': rec['productName'],
                            'img_url': rec['imageURL'],
                            })
                episodes.append({'date': rec['startTime'], 
                                'desc': 'I purchased the book "%s" from Libby' % rec['productName'],
                                'details': 'I purchased the book "%s" with an image url %s from Libby' % (rec['productName'], rec['imageURL'])})
            elif rec['source'] == 'AmazonKindle':
                if rec['productName'] in ['Kindle Unlimited', 'Prime Membership Fee', 'Audible Premium Plus']:
                    continue
                asin = self.product_image_index[rec['productName']]
                url = f'https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US&ASIN={asin}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL250'
                output.append({'time': rec['startTime'],
                            'book_name': rec['productName'],
                            'img_url': url,
                            })
                episodes.append({'date': rec['startTime'], 
                                'desc': 'I purchased the book "%s" from Amazon Kindle' % rec['productName'],
                                'details': 'I purchased the book "%s" with an image url %s from Libby' % (rec['productName'], url)})

        # output to JSON
        json.dump(output, open(os.path.join(self.app_path, 'books.json'), 'w'), indent=2)

        # output to CSV
        output_path = os.path.join(self.app_path, 'books.csv')
        pd.DataFrame.from_records(output).to_csv(output_path, index=False)
        
        return episodes


    def create_places_table(self, table: List):
        """Create a list of places episodes.
        """
        output = []
        episodes = []
        for rec in table:
            if rec['source'] == 'GoogleTimeline':
                if len(rec['locations']) == 1:
                    end_index = 0
                else:
                    end_index = 1

                output.append({'start_time': rec['startTime'],
                            'end_time': rec['endTime'],
                            'textDescription': rec['textDescription'],
                            'start_address': rec['locations'][0],
                            'start_lat': rec['lat_lon'][0][0],
                            'start_long': rec['lat_lon'][0][1],
                            'end_address': rec['locations'][end_index],
                            'end_lat': rec['lat_lon'][end_index][0],
                            'end_long': rec['lat_lon'][end_index][1],
                            })
                episodes.append({'date': rec['startTime'], 
                                'desc': rec['textDescription'],
                                'details': 'The event starts at %s and ends at %s. The description of this event is %s. The event starts at the location %s (%s, %s) and ends at the location %s (%s, %s).' % \
                                    (rec['startTime'], rec['endTime'], rec['textDescription'], 
                                    rec['locations'][0], rec['lat_lon'][0][0], 
                                    rec['lat_lon'][0][1], 
                                    rec['locations'][end_index], 
                                    rec['lat_lon'][end_index][0], 
                                    rec['lat_lon'][end_index][1])
                                })
                # print(rec)
                # break
            elif rec['source'] == 'GooglePhotos':
                if len(rec['locations']) == 1:
                    end_index = 0
                else:
                    end_index = 1

                output.append({'start_time': rec['startTime'],
                            'end_time': rec['endTime'],
                            'textDescription': "from Google Photo", # to be replaced by image caption
                            'start_address': rec['locations'][0],
                            'start_lat': rec['lat_lon'][0][0],
                            'start_long': rec['lat_lon'][0][1],
                            'end_address': rec['locations'][end_index],
                            'end_lat': rec['lat_lon'][end_index][0],
                            'end_long': rec['lat_lon'][end_index][1],
                            })
                episodes.append({'date': rec['startTime'], 
                                'desc': rec['locations'][0],
                                'details': 'The event starts at %s and ends at %s. The event starts at the location %s (%s, %s) and ends at the location %s (%s, %s).' % \
                                    (rec['startTime'], rec['endTime'], 
                                    rec['locations'][0], rec['lat_lon'][0][0], 
                                    rec['lat_lon'][0][1], 
                                    rec['locations'][end_index], 
                                    rec['lat_lon'][end_index][0], 
                                    rec['lat_lon'][end_index][1])})
                # break
        # output to JSON
        json.dump(output, open(os.path.join(self.app_path, 'places.json'), 'w'), indent=2)

        # output to CSV
        output_path = os.path.join(self.app_path, 'places.csv')
        pd.DataFrame.from_records(output).to_csv(output_path, index=False)

        return episodes


    def create_streaming_table(self, table: List):
        """Create a list of streaming episodes.
        """
        output = []
        episodes = []

        cid = os.environ['SPOTIFY_TOKEN']
        secret = os.environ['SPOTIFY_SECRET']
        client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        for rec in table:
            if rec['source'] == 'Spotify':
                link = ""
                try:
                    res = spotify.search(q=f"artist: {rec['artist']} track:{rec['track']}" , type="track", limit=5)
                    if 'tracks' in res and 'items' in res['tracks']:
                        for item in res['tracks']['items']:
                            if 'external_urls' in item:
                                link = item['external_urls']['spotify']
                            else:
                                print(item)
                except:
                    print("Spotify Exception: " + str(rec['artist']) + " " + str(rec['track']))

                output.append({'start_time': rec['startTime'],
                            'end_time': rec['endTime'],
                            'artist': rec['artist'],
                            'track': rec['track'],
                            'playtimeMs': rec['playtimeMs'],
                            'spotify_link': link
                            })
                episodes.append({'date': rec['startTime'], 
                                'desc': "I listen to %s from %s on Spotify" % (rec['track'], rec['artist']),
                                'details': "From %s to %s, I listen to %s from %s on Spotify. The length of the track is %d ms. Here's the link: %s" % \
                                    (rec['startTime'], rec['endTime'], rec['track'], rec['artist'], rec['playtimeMs'], link)})

        # output to JSON
        json.dump(output, open(os.path.join(self.app_path, 'streaming.json'), 'w'), indent=2)

        # output to CSV
        output_path = os.path.join(self.app_path, 'streaming.csv')
        pd.DataFrame.from_records(output).to_csv(output_path, index=False)
        return episodes

    
    def create_exercise_table(self, table: List):
        """Create a list of exercise episodes.
        """
        output = []
        episodes = []
        for rec in table:
            if rec['source'] == 'AppleHealth':
                output.append({'start_time': rec['startTime'],
                            'end_time': rec['endTime'],
                            'textDescription': rec['textDescription'],
                            'duration': rec['duration'],
                            'distance': rec['distance'],
                            'calories': rec['calories'],
                            'outdoor': rec['outdoor'],
                            'temperature': rec['temperature']})
                if rec['outdoor'] == 1:
                    outdoor = 'outdoor'
                else:
                    outdoor = 'indoor'
                
                if len(rec['temperature']) > 0:
                    outdoor += ' and the temperature was about %s' % rec['temperature']

                episodes.append({'date': rec['startTime'], 
                                'desc': 'I exercised by' + rec['textDescription'][6:],
                                'details': 'From %s to %s, I exercised by %s. Duration of this exercise was %s, distance was %s, and calories are %s. I did the exercise %s.' % 
                                    (rec['startTime'], rec['endTime'], rec['textDescription'][6:], 
                                    rec['duration'], rec['distance'], rec['calories'], outdoor)
                                })

        # output to JSON
        json.dump(output, open(os.path.join(self.app_path, 'exercise.json'), 'w'), indent=2)

        # output to CSV
        output_path = os.path.join(self.app_path, 'exercise.csv')
        pd.DataFrame.from_records(output).to_csv(output_path, index=False)
        return episodes
    

    def create_purchase_table(self, table: List):
        """Create the purchase episodes.
        """
        output = []
        episodes = []
        for rec in table:
            if rec['source'] == 'Amazon':
                output.append({'time': rec['startTime'],
                            'purchase_id': rec['purchase_id'],
                            'productName': rec['productName'],
                            'productPrice': rec['productPrice'],
                            'productQuantity': rec['productQuantity']})
                episodes.append({'date': rec['startTime'], 
                                'desc': 'I purchased %s from Amazon' % rec['productName'], 
                                'details': 'On %s, I purchased %s from Amazon. The product prise is %s and product quantity is %s.' % 
                                (rec['startTime'], rec['productName'], rec['productPrice'], rec['productQuantity'])})
        # output to JSON
        json.dump(output, open(os.path.join(self.app_path, 'purchase.json'), 'w'), indent=2)

        # output to CSV
        output_path = os.path.join(self.app_path, "purchase.csv")
        pd.DataFrame.from_records(output).to_csv(output_path, index=False)
        return episodes

    
if __name__ == '__main__':
    creator = EpisodeCreator()
    creator.create_all_episodes()