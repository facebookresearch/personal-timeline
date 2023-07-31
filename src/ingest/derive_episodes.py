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



import os
import langchain
import json
import pandas as pd
import numpy as np

from math import sin, cos, sqrt, atan2, radians
from typing import List
from langchain.llms import OpenAI
from langchain.cache import SQLiteCache
from tqdm import tqdm

langchain.llm_cache = SQLiteCache(database_path=".langchain.db")


class EpisodeDeriver:
    def __init__(self, app_path='personal-data/app_data/'):
        self.app_path = app_path
        self.llm = OpenAI(temperature=0)
        self.places = pd.read_csv(os.path.join(app_path, "places.csv"))
        self.places = self.places.sort_values(by="start_time")
        # places.to_csv("places.csv", index=False)

    def run(self):
        """Run the whole pipeline.
        """
        json_path = os.path.join(self.app_path, "trips.json")
        if os.path.exists(json_path):
            print("Derived trips found.")
        else:
            print("Start segmenting trips.")
            trips = self.derive_trips(self.places)

            print("Start summarizing trips.")
            output = self.make_trip_table(trips, self.places)

            json.dump(output, open(json_path, 'w'))
            pd.DataFrame(output).to_csv(os.path.join(self.app_path, "trips.csv"), index=False)

    def distance(self, latlon_a, latlon_b):
        """Compute the distance (in km) between two lat/lon pairs.
        """
        # Approximate radius of earth in km
        R = 6373.0

        lat1 = radians(latlon_a[0])
        lon1 = radians(latlon_a[1])
        lat2 = radians(latlon_b[0])
        lon2 = radians(latlon_b[1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return  R * c

    def get_center(self, lat_lons):
        """Compute the center (mean) of a list of lat/lons.
        """
        return (np.mean([ll[0] for ll in lat_lons]),
                np.mean([ll[1] for ll in lat_lons]))

    def add_tag(self, segments: List[dict], d=200):
        """Tag a list of segments as home/trip/transit
        """
        # find short segment
        for seg in segments:
            if len(seg["ids"]) <= 5:
                seg["tag"] = 'transit'

        # find home cluster
        known_centers = []
        for idx, seg in enumerate(segments):
            center = self.get_center(seg["lat_lons"])
            found = False
            for i in range(len(known_centers)):
                if self.distance(known_centers[i][0], center) <= d:
                    known_centers[i][1].append(idx)
                    found = True
                    break
            
            if not found:
                known_centers.append([center, [idx]])
        
        max_cnt = max([len(indices) for _, indices in known_centers])
        for _, indices in known_centers:
            if len(indices) == max_cnt:
                for idx in indices:
                    segments[idx]["tag"] = "home"
        
        for seg in segments:
            if "tag" not in seg:
                seg["tag"] = "trip"


    def cluster(self, places: pd.DataFrame, d=200):
        """Cluster a list of lat/lon based on distances.

        Args:
            places (pd.DataFrame): the places table
            d (float): the distance upper bound for each cluster
        
        Returns:
            List: A list of segments. Each segment is one trip.
        """
        start = 0
        segments = []
        lats = list(places['start_lat'])
        longs = list(places['start_long'])
        addresses = list(places['start_address'])
        ids = list(places['id'])

        while start < len(places):
            end = start
            start_lat_lon = lats[start], longs[start]
            lat_lons = [(lats[start], longs[start])]
            while end + 1 < len(places) and self.distance(start_lat_lon, (lats[end+1], longs[end+1])) <= d:
                end += 1
                lat_lons.append((lats[end], longs[end]))
            
            segments.append({"start_idx": start, 
                            "end_idx": end,
                            "addresses": addresses[start:end+1],
                            "ids": ids[start:end+1],
                            "lat_lons": lat_lons})
            start = end + 1

        self.add_tag(segments, d=d)
        return segments


    def derive_trips(self, places: pd.DataFrame):
        """Derive a set of trips from a sequence of location tracking.
        """
        places = places.sort_values(by="start_time")
        print('number of places =', len(places))

        # remove locations at (0, 0)
        places = places[places['start_address'] != "Soul Buoy"]
        print('number of non-(0,0) places =', len(places))

        return self.cluster(places)


    def summarize(self, input):
        """Use llm to detech what places are visited for each trip.
        """
        return self.llm(input + "\n\nWhich country did I visit?\nWhich states/provinces did I visit?\nWhich cities/towns did I visit?\nWhat places did I visit?\nAnswer in 4 lines with line breaks.\n\n")

    def summarize_oneline(self, input):
        """Summarize the trip into a trip title using llm.
        """
        return self.llm(input + " Can you summarize the country, states/provinces, cities/towns, and places I have been to?")

    def describe_place(self, address):
        """Ask llm to describe what is in an address.
        """
        return self.llm("Can you describe what is in this address in one sentence: " + address)

    def summarize_day(self, places, details="low"):
        """Summarize places visited in a day.
        """
        prompt = "Here's the list of places that I have been to during a trip:\n"
        idx = 0
        places = places.to_dict('records')
        while idx < len(places):
            address = places[idx]['start_address']
            start_time = places[idx]['start_time']
            end_time = places[idx]['end_time']
            while idx + 1 < len(places) and places[idx]['start_address'] == places[idx+1]['start_address']:
                idx += 1
                end_time = places[idx]['end_time']
            
            # process address
            addr_desc = self.describe_place(address)
            # print(addr_desc)
            if start_time == end_time:
                prompt += '%s: %s\n\n' % (start_time, addr_desc.strip())
            else:
                prompt += 'from %s to %s: %s\n\n' % (start_time, end_time, addr_desc.strip())
            idx += 1
        
        prompt += "\nHelp me summarize my trip to another person. Highlight significant places (e.g., restaurants, attractions, cities, countries) that I have visited. Try to break down the trip summary by days.\n"
        if details == 'high':
            prompt += "Make sure to include as many details as possible."
        else:
            prompt += "Write a summary in at most 100 words."

        print(prompt)
        res = self.llm(prompt)
        # print(res)
        return res


    def make_trip_table(self, trips, places):
        """Create the trip episodes.
        """
        output = []
        for trip in tqdm(trips):
            if trip["tag"] == 'trip':
                start_id = trip["ids"][0]
                end_id = trip["ids"][-1]

                trip_places = places[places['id'].isin(trip['ids'])]
                text_summary_oneline = self.summarize_day(trip_places, details="low")
                text_summary = self.summarize_day(trip_places, details="high")

                descriptions = [str(places[places["id"] == idx]["textDescription"].values[0]) for idx in trip["ids"] if \
                                "Google Photo" not in str(places[places["id"] == idx]["textDescription"].values[0])]
                
                if len(descriptions) == 0:
                    descriptions = [str(places[places["id"] == idx]["start_address"].values[0]) for idx in trip["ids"]]
                    descriptions = list(set(descriptions))[:60]

                try:
                    summary = self.summarize("\n".join(descriptions)).strip()
                    # summary_oneline = self.summarize_oneline("\n".join(descriptions)).strip()
                except:
                    print(descriptions)
                    continue

                lines = summary.split('\n')
                country = states_provinces = cities_towns = places_visited = ""
                if len(lines) > 0:
                    country = lines[0]
                if len(lines) > 1:
                    states_provinces = lines[1]
                if len(lines) > 2:
                    cities_towns = lines[2]
                if len(lines) > 3:
                    places_visited = lines[3]

                rec = {"start_time": str(places[places["id"] == start_id]["start_time"].values[0]),
                    "end_time": str(places[places["id"] == end_id]["end_time"].values[0]),
                    "textDescription": text_summary_oneline,
                    "details": text_summary,
                    "country": country,
                    "states_provinces": states_provinces,
                    "cities_towns": cities_towns,
                    "places": places_visited}
                output.append(rec)
        print("Found trips:", len(output))
        return output

if __name__ == '__main__':
    deriver = EpisodeDeriver()
    deriver.run()