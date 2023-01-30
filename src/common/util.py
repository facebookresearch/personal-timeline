import datetime
from pathlib import Path

import pytz
import geopy
import json

from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from sklearn.metrics.pairwise import haversine_distances
from math import radians
from typing import Union, List
from geopy import Location

from src.common.geo_helper import GeoHelper

EPOCH = datetime(1970,1,1)

# output a string such as "Showing photo 17 of 24"
def xOfy(i, total):
    result = "Showing photo " + str(i+1) + " of " + str(total)
    return result

#extract a tuple of year/month/day from ISO format
def extractYMD(date):
    year = int(date[0:4])
    month = int(date[5:7])
    dom = int(date[8:10])
    return ((year, month, dom))

#extracting a month or day-of-month from ISO format
def extract_month(date):
    return(date[5:7])

def extract_DOM(date):
    return(date[8:10])

def sameMonth(date1, date2):
    d1 = date1[0:7]
    d2 = date2[0:7]
    return (d1 == d2)

# truncates a string number to a string with digits after the decimal
def truncateStringNum(num,digits):
    f = float(num) * (10 ** digits)
    i = int(f) / (10 ** digits)
    if digits == 0:
        j = int(i)
        return (str(j))
    else:
        return (str(i))

def dayToDate(num):
    result = datetime(1970,1,1) + timedelta(days=num)
    print (result)
    return (str(result))

def daysSinceEpoch(date):
    #print(date)
    year, month, dom = extractYMD(date)
#    diff = (datetime.datetime(year, month, dom) - datetime.datetime(1970,1,1)).days
    diff = (datetime(year, month, dom) - datetime(1970,1,1)).days
    return (int(diff))

#return the day that happens n days after the epoc (1970/1/1)
def nDaysAfterEpoch(n):
    epoch_day = datetime(1970,1,1)
    new_day = epoch_day + timedelta(days=n)
    return (str(new_day)[0:10])

# extract the time of day from ISO format
def extractTOD(s):
    return s[11:19]

# given a time (ISO text), origin and target timezones (text), convert the time
# from the origin to target timezone.
def convertToTimezone (t, tz_origin, tz_target):
    given_time = t[0:19]
    time_object = datetime.fromisoformat(given_time)
    tz1 = pytz.timezone(tz_origin)
    tz2 = pytz.timezone(tz_target)
    origin_date = tz1.localize(time_object)
    target_date = tz2.normalize(origin_date)
    #print("converting time t from tz origin to tz-target: result")
    #print (t, tz_origin, tz_target)
    #print (target_date)
    return(str(target_date))

#given a lat/long, return the string for its timezon
def convertlatlongToTimezone(lat_string, long_string):
    tf = TimezoneFinder()
    longitude = float(long_string)/1E7
    latitude = float(lat_string)/1E7
    timezone_str = str(tf.timezone_at(lng=longitude, lat=latitude))
    return (timezone_str)

def convertOutOfE7(s):
    return str(float(s)/1E7)

def extractYMDHM(date):
    year = int(date[0:4])
    month = int(date[5:7])
    dom = int(date[8:10])
    hour = int(date[11:13])
    minute = int(date[14:16])
    #print (dom, hour, minute)
    return ((year, month, dom, hour, minute))


def dict_to_json(dict):
    new_dict = {}
    for key in dict:
        json_str = "[ "
        cnt = 0
        for obj in dict[key]:
            cnt = cnt +1
            if cnt > 1:
                json_str = json_str + " , "
            json_str = json_str + obj.toJson()
        json_str = json_str + " ]"
        new_dict[key]= json_str
    return(new_dict)


def distance(latlon_a, latlon_b):
    """Compute distance in km of two latlon pairs.
    """
    radians_a = [radians(_) for _ in latlon_a]
    radians_b = [radians(_) for _ in latlon_b]
    result = haversine_distances([radians_a, radians_b])
    return result[1, 0] * 6371000 / 1000  # multiply by Earth radius to get kilometers


geolocator = GeoHelper()
geo_cache = {}
try:
    translate_geo_cache = {} #dbm.open('personal-data/app_data/geo_cache', 'c')
except:
    print("translate_geo_cache", translate_geo_cache.keys())
cwd = str(Path().absolute())
user_info = json.load(open(cwd+"/src/common/user_info.json"))
default_location = user_info["address"]



def translate_place_name(place_name: str) -> str:
    """Translate a place name to English.
    """
    # print(place_name)
    result = place_name

    if place_name in translate_geo_cache:
        result = translate_geo_cache[place_name]#.decode('utf8')
        # translate_geo_cache.close()
        return result

    translated_addr = geolocator.geocode(place_name, language="en")
    if translated_addr is not None:
        result = translated_addr.address
        translate_geo_cache[place_name] = result
    # translate_geo_cache.close()
    return result

def is_home(loc: Location):
    """Check if a location is home (within 100km)."""
    try:
        home = get_coordinate(default_location)
        loc = get_coordinate(loc)
        return distance(home, loc) <= 100.0
    except:
        return True

def get_location_attr(loc: Location, attr: Union[str, List]):
    """Return an attribute (city, country, etc.) of a location"""
    if loc is None:
        return ""

    addr = loc
    if 'address' not in addr.raw:
        cood = (loc.latitude, loc.longitude)
        if cood not in geo_cache:
            addr = geolocator.calculateLocation(loc.latitude, loc.longitude)
            geo_cache[cood] = addr
        else:
            addr = geo_cache[cood]

    if 'address' in addr.raw:
        if isinstance(attr, str):
            attr = [attr]

        for attr_item in attr:
            if attr_item in addr.raw['address']:
                return addr.raw['address'][attr_item]

    return ""

# create trip segments: consecutive days with start / end = home
# geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
# geo_cache = {}
#default_location = json.load(open('user_info.json'))["address"] # "United States"

def str_to_location(loc: str):
    """Convert a string to geolocation."""
    if loc in geo_cache:
        return geo_cache[loc]
    else:
        geoloc = geolocator.geocode(loc.replace(';', ', '), language='en')
        if geoloc is None:
            geoloc = geolocator.geocode(default_location, language='en') # maybe use home as default?

        geo_cache[loc] = geoloc
        return geoloc


def get_coordinate(loc: Union[str, Location]):
    """Get coordinate of a location."""
    if isinstance(loc, Location):
        return loc.latitude, loc.longitude

    geoloc = str_to_location(loc)
    return geoloc.latitude, geoloc.longitude

