import json
import os
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from code.objects.LLEntry_obj import LLEntry
import pytz
from pytz import timezone
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
from util import *
import time
from geopy.geocoders import Nominatim

# This is where the photos and their jsons sit

OUTPUT_FILE = "google_timeline_data.json"
GTIMELINE_DIR = "2019"
# This is where the intermediate json files sit
ROOT_DIRECTORY = "~/Documents/code/pim/"
SOURCE = "Google Timeline"
ORIGIN_TIMEZONE = str(pytz.utc)
global geolocator
geolocator = Nominatim(user_agent="pim_photo")

# se: True if it's for start, False for end
# lat/long are strings

def calculateLocationFromLatLong(lat, lon):
    #print ("lat is ", lat)
    time.sleep(1)
    location = geolocator.reverse(str(lat)+","+str(lon), addressdetails=True)
    return (location)


def updateLocation(obj, se, lat, lon):
    loc = calculateLocationFromLatLong(lat, lon) 
    if se:
        obj.startLocation = str(loc)
    else:
        obj.endLocation = str(loc)
    if loc is not None: 
        if "country" in loc.raw["address"]:
            if se:
                obj.startCountry = loc.raw["address"]["country"]
            else:
                obj.endCountry = loc.raw["address"]["country"]

        if "city" in loc.raw["address"]:
            if se:
                obj.startCity = loc.raw["address"]["city"]
            else:
                obj.endCity = loc.raw["address"]["city"]
        if "state" in loc.raw["address"]:
            if se:
                obj.startState = loc.raw["address"]["state"]
            else:
                obj.endState = loc.raw["address"]["state"]

def generate_textDescription(details):
    #print (details)
    result = details["start"] + ": "
    if "activity" not in details: 
        return (result+ "unidentified activity")
    result = result + details["activity"] + " "
    if "duration" in details:
        result = result + truncateStringNum(details["duration"],0) + " minutes "
    if "distance" in details:
        distanceNum = truncateStringNum(details["distance"],2)
        if distanceNum != "0.0":
            result = result + distanceNum  + " miles "
    #if details["indoor"] != "0":
#        result = result + "(indoors)"


def placeVisitExtract(visit):
    #print ("in place visit extract")
    wtype = "base:visit"
    start = visit["duration"]["startTimestamp"][0:19]
    
    start_lat = visit["location"]["latitudeE7"]
    start_long = visit["location"]["longitudeE7"]
    target_timezone = convertlatlongToTimezone(start_lat, start_long)
    experienced_startTime = convertToTimezone (start, ORIGIN_TIMEZONE, target_timezone)
    print ("visit: lat long, start, target_timezone, experiencedStartTime")
    print (start_lat)
    print (start_long)
    print (start)
    print (target_timezone)
    print (experienced_startTime)
    obj = LLEntry(wtype, experienced_startTime, SOURCE)
    startTOD = experienced_startTime[11:19]
    obj.startTimeOfDay = startTOD
    textDescription = startTOD[0:5] + ": "
    if "location" in visit:
        obj.startLocation = visit["location"]["name"]
        textDescription = textDescription + "visit to " + visit["location"]["name"]
    
    if "duration" in visit:
       obj.endTime =  visit["duration"]["endTimestamp"][0:19]
       experienced_endTime = convertToTimezone (visit["duration"]["endTimestamp"][0:19],
                                             ORIGIN_TIMEZONE, target_timezone)
       obj.endTime =  experienced_endTime
       obj.endTimeOfDay =  experienced_endTime[11:19]

       tstart = datetime.fromisoformat(obj.startTime)
       tend = datetime.fromisoformat(obj.endTime)
       dur = tend-tstart
       obj.duration = str(dur)
       textDescription = textDescription + " (duration: " + obj.duration + ")"

    obj.textDescription = textDescription
    print ("TEXT DESCRIPTION:  ",  obj.textDescription)

    return obj

def activitySegmentExtract(activity):
    print ("in activity extract")
    translation = {"IN_PASSENGER_VEHICLE": "drive",
               "WALKING": "walk",
                   "MOTORCYCLING": "motorcycle",  "IN_BUS": "bus",
                   "IN_SUBWAY": "subway", "CYCLING": "cycling", 
               "FLYING": "fly"}
    textDescription = " "
    if "activityType" not in activity:
        print ("activityType not in Activity")
        print (activity)
    if "activityType" in activity:
        if activity["activityType"] in translation:
            wtype = "base:" + translation[activity["activityType"]]
            textActivity = translation[activity["activityType"]]
        else:
            wtype = "base:" + activity["activityType"]
            textActivity = "Unrecognized activity"
            print ("add new activity type to dictionary ", activity["activityType"]) 

    start = activity["duration"]["startTimestamp"][0:19]

    start_lat = convertOutOfE7(activity["startLocation"]["latitudeE7"])
    start_long = convertOutOfE7(activity["startLocation"]["longitudeE7"])
    end_lat = convertOutOfE7(activity["endLocation"]["latitudeE7"])
    end_long = convertOutOfE7(activity["endLocation"]["longitudeE7"])

    target_timezone = convertlatlongToTimezone(activity["startLocation"]["latitudeE7"], \
                                               activity["startLocation"]["longitudeE7"])
    experienced_startTime = convertToTimezone (start, ORIGIN_TIMEZONE, target_timezone)
    print ("activity: lat long, start, target_timezone, experiencedStartTime")
    print (activity["startLocation"]["latitudeE7"])
    print (activity["startLocation"]["longitudeE7"])
    print (start)
    print (target_timezone)
    print (experienced_startTime)
        
    startTOD = experienced_startTime[11:19]
    textDescription = startTOD[0:5] +  ": "  + textActivity
    obj = LLEntry(wtype, experienced_startTime, SOURCE)
    updateLocation(obj, True, start_lat, start_long)
    updateLocation(obj, False, end_lat, end_long)
    obj.startTimeOfDay = startTOD
    experienced_endTime = convertToTimezone (activity["duration"]["endTimestamp"][0:19], ORIGIN_TIMEZONE, target_timezone)
    obj.endTime =  experienced_endTime
    obj.endTimeOfDay =  experienced_endTime[11:19]
    
    tstart = datetime.fromisoformat(obj.startTime)
    tend = datetime.fromisoformat(obj.endTime)
    dur = tend-tstart
    obj.duration = str(dur)
    textDescription = textDescription + " (duration: " + obj.duration + ")"

    if "name" in activity["endLocation"]:
        #print(activity["endLocation"]["name"])
        obj.endLocation = activity["endLocation"]["name"]
        textDescription = textDescription + " ended at " + obj.endLocation
    if "distanceMeters" in activity: 
        obj.distance = activity["distanceMeters"]
        textDescription = textDescription + " distance: " + obj.distance

    obj.textDescription = textDescription
    print ("TEXT DESCRIPTION:  ",  obj.textDescription)
    return obj

cwd = Path() # or Path('.')

json_filepath = cwd / GTIMELINE_DIR
json_dir =  os.listdir(json_filepath)
# print(json_dir)
count = 0
output_json = '{ "solrobjects": [ '  
output_dir = { "visits": 0, "activity":0}

for json_file in json_dir:
    #print (json_file)
    path = json_filepath / json_file
    #print(path)
    with open(path, 'r') as f_json:
      r = f_json.read()
      data  = json.loads(r)


    for i in data['timelineObjects']:
        count = count +1
        if count > 1:
            output_json = output_json + " , "

        key_list = [*i.keys()]
        if key_list[0] == "placeVisit":
            output_json = output_json + placeVisitExtract(i["placeVisit"]).toJson()
            output_dir["visits"] = output_dir["visits"] +1 
        elif key_list[0] == "activitySegment":
            output_json = output_json + activitySegmentExtract(i["activitySegment"]).toJson()
            output_dir["activity"] = output_dir["activity"] +1 
        else:
            print ("Can't recognize key", key_list[0])

output_json = output_json + " ] } "
#print (output_json)
#print (output_dir)
print ("Number of records is: ")
print (count )

with open(OUTPUT_FILE, 'w') as outfile:
    outfile.write(output_json)
    

     
