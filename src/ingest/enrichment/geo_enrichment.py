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



from typing import List

import pickle

from tqdm import tqdm

from src.common.geo_helper import GeoHelper
from src.common.objects.LLEntry_obj import LLEntry
from geopy.location import Location

from src.common.persistence.personal_data_db import PersonalDataDBConnector

class LocationEnricher:
    def __init__(self):
        self.geo_helper = GeoHelper()
        self.db = PersonalDataDBConnector()

    def enrich(self, incremental:bool=True):
        select_cols = "id, data"
        select_count = "count(*)"
        where_clause={"data": "is not NULL"}
        if incremental:
            where_clause["location_done"] = "=0"
        count_res = self.db.search_personal_data(select_count, where_clause)
        pending = count_res.fetchone()
        if pending is None:
            print("No pending location enrichments")
            return
        # print("Total enrichments to be done: ", pending[0])
        res = self.db.search_personal_data(select_cols, where_clause)
        count = 0
        for row in tqdm(res.fetchall()):
            row_id = int(row[0])
            data:LLEntry = pickle.loads(row[1])
            #print("data.lat_lon", data.__dict__)
            entry_location: List[Location] = []
            for lat_lon_entry in data.lat_lon:
                entry_location.append(self.geo_helper.calculateLocation(lat_lon_entry[0], lat_lon_entry[1]))
            #print("Updating location to::: ", photo_location.raw)
            if len(entry_location) > 0:
                count += 1
                self.db.add_or_replace_personal_data({"location": entry_location, "location_done": 1, "id": row_id}, "id")
        print("Cache Hits: ", self.geo_helper.reverse_cache_hits, " Cache misses: ", self.geo_helper.reverse_cache_miss)
        print("Geo Processing completed for ", count, " entries")