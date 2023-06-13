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