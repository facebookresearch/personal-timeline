import pytz
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
import datetime
from datetime import datetime

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

ORIGIN_TIMEZONE = str(pytz.utc)

global geolocator
geolocator = Nominatim(user_agent="pim_photo")

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=5)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=5)

class LocationTimeEnricher:
    def calculateLocation(latitude: float, longitude: float):
        #time.sleep(1)
        # location = geolocator.reverse(str(latitude)+","+str(longitude), addressdetails=True)
        location = reverse(str(latitude) + "," + str(longitude), addressdetails=True)

        # geolocator = Nominatim(user_agent="application")

        # reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

        # location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)

        #print(str(location))
        return (location)


    def calculateExperiencedTimeRealAndUtc(latitude: float, longitude: float, timestamp: int):
        result = ""
        # get timestamp
        utc = pytz.utc
        utc_dt = utc.localize(datetime.utcfromtimestamp(timestamp))
        # translate lat/long to timezone
        tf = TimezoneFinder()

        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        # print(timezonetf)
        tzo = tzwhere.tzwhere()

        #    if latitude == 0.0 and longitude == 0.0:
        #        timezone_str = "America/Los_Angeles"
        #    else:
        #        timezone_str = tzo.tzNameAt(latitude, longitude) # real coordinates
        print(timezone_str)
        real_timezone = pytz.timezone(timezone_str)
        real_date = real_timezone.normalize(utc_dt.astimezone(real_timezone))
        print("converted into: ", real_date)
        return str(real_date), str(utc_dt)

