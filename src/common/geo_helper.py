import pickle

import pytz

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from geopy.location import Location

from src.common.persistence.key_value_db import CacheDBConnector

ORIGIN_TIMEZONE = str(pytz.utc)

global reverse_geolocator
global geolocator

reverse_geolocator = Nominatim(user_agent="pim_photo_import")
geolocator = Nominatim(user_agent="pim_photo_ui")

reverse = RateLimiter(reverse_geolocator.reverse, min_delay_seconds=1)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

class GeoHelper:
    geo_reverse_cache = {}
    geo_cache = {}

    def __init__(self):
        self.cache_db = CacheDBConnector()
        self.reverse_cache_hits=0
        self.reverse_cache_miss=0
        self.cache_hits = 0
        self.cache_miss = 0

    def cache_key(self, address:str):
        return address

    def reverse_cache_key(self, latitude:float, longitude:float):
        return str(latitude)+","+str(longitude)

    def calculateLocation(self, latitude: float, longitude: float) -> Location:
        if latitude is None or longitude is None:
            return None
        reverse_cache_key = self.reverse_cache_key(latitude, longitude)
        if reverse_cache_key in GeoHelper.geo_reverse_cache.keys():
            cached_loc = GeoHelper.geo_reverse_cache[reverse_cache_key]
            #print(reverse_cache_key, " found in location cache. Returning ", str(cached_loc))
            self.reverse_cache_hits+=1
            return cached_loc
        location = reverse(str(latitude) + "," + str(longitude), addressdetails=True)
        # location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)
        #print("Location:: ", str(location))
        GeoHelper.geo_reverse_cache[reverse_cache_key] = location
        self.reverse_cache_miss += 1
        return location

    def geocode(self, address:str, language:str="en") -> str:
        if address is None or address=="":
            return None
        cache_key = self.cache_key(address)
        cached_loc = self.cache_db.get(cache_key, "geo_cache")
        if cached_loc is not None:
            cached_loc_unpickled = pickle.loads(cached_loc[0])
            # print(cache_key, " found in location cache. Returning ", cached_loc_unpickled)
            self.cache_hits += 1
            return cached_loc_unpickled
        else:
            # print(cache_key, " not found in location cache")
            # Fetch value
            location:Location = geocode(address, language=language)
            # Make entry into cache
            pickled_object = pickle.dumps(location)
            self.cache_db.put(cache_key, pickled_object, "geo_cache")
            self.cache_miss += 1
            return location

# gh = GeoHelper()
# print(gh.geocode("Bangalore, India"))
# print(gh.geocode("Bangalore, India"))