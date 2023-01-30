import pytz

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from geopy.location import Location
from functools import partial

ORIGIN_TIMEZONE = str(pytz.utc)

global geolocator
geolocator = Nominatim(user_agent="pim_photo")

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=3)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

class GeoHelper:
    geo_cache = {}

    def __init__(self):
        self.cache_hits=0
        self.cache_miss=0

    def cache_key(self, latitude:float, longitude:float):
        return str(latitude)+","+str(longitude)

    def calculateLocation(self, latitude: float, longitude: float) -> Location:
        if latitude is None or longitude is None:
            return None
        cache_key = self.cache_key(latitude, longitude)
        if cache_key in GeoHelper.geo_cache.keys():
            cached_loc = GeoHelper.geo_cache[cache_key]
            #print(cache_key, " found in location cache. Returning ", str(cached_loc))
            self.cache_hits+=1
            return cached_loc
        location = reverse(str(latitude) + "," + str(longitude), addressdetails=True)
        # location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)
        #print("Location:: ", str(location))
        GeoHelper.geo_cache[cache_key] = location
        self.cache_miss += 1
        return location

    def geocode(self, address:str, language:str="en"):
        location = partial(geocode, (address, language))()
        # print("Geocoded location for", address, ":", location)
        return location

gh = GeoHelper()
print(gh.geocode("Bangalore, India"))