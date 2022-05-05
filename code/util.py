
import json
import os
from pathlib import Path
import datetime
from datetime import datetime, timedelta
from datetime import timezone
from json_obj import LLEntry
import xml.etree.ElementTree as ET
import pytz
from pytz import timezone
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
import time
from geopy.geocoders import Nominatim

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

