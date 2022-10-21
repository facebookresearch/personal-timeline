import pytz
import pickle

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm

from src.objects.LLEntry_obj import LLEntry
from geopy.location import Location

from src.persistence.personal_data_db import PersonalDataDBConnector

ORIGIN_TIMEZONE = str(pytz.utc)

global geolocator
geolocator = Nominatim(user_agent="pim_photo")

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

class LocationEnricher:
    def __init__(self):
        self.cache = {}
        self.cache_hits=0
        self.cache_miss=0
        self.db = PersonalDataDBConnector()

    def cache_key(self, latitude:float, longitude:float):
        return str(latitude)+","+str(longitude)
    def calculateLocation(self, latitude: float, longitude: float) -> Location:
        cache_key = self.cache_key(latitude, longitude)
        if cache_key in self.cache.keys():
            cached_loc = self.cache[cache_key]
            #print(cache_key, " found in location cache. Returning ", str(cached_loc))
            self.cache_hits+=1
            return cached_loc
        location = reverse(str(latitude) + "," + str(longitude), addressdetails=True)
        # location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)
        #print("Location:: ", str(location))
        self.cache[cache_key] = location
        self.cache_miss += 1
        return location

    def enrich(self):
        select_cols = "id, data"
        select_count = "count(*)"
        where_clause={"location_done": "=0", "data": "is not NULL"}
        count_res = self.db.search_photos(select_count, where_clause)
        pending = count_res.fetchone()
        if pending is None:
            print("No pending location enrichments")
            return
        # print("Total enrichments to be done: ", pending[0])
        res = self.db.search_photos(select_cols, where_clause)
        count = 0
        for row in tqdm(res.fetchall()):
            count +=1
            row_id = int(row[0])
            data:LLEntry = pickle.loads(row[1])
            photo_location:Location = self.calculateLocation(data.latitude, data.longitude)
            #print("Updating location to::: ", photo_location.raw)
            self.db.update_photos(row_id, {"location": photo_location, "location_done": '1'})
        print("Cache Hits: ", self.cache_hits," Cache misses: ", self.cache_miss)
        print("Geo Processing completed for ", count, " entries")