import json
import os
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from code.objects.LLEntry_obj import LLEntry
import xml.etree.ElementTree as ET
import pytz
from util import *

APPLE_INPUT_DATA_FILE = "iwatch.xml"
OUTPUT_FILE = "applehealth_data.json"
SOURCE = "AppleHealth"
TYPE = "base/"
ORIGIN_TIMEZONE = "America/Los_Angeles"
global current_timezone
global activityTranslation


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


    return (result)

cwd = Path()
input_data_path = cwd / APPLE_INPUT_DATA_FILE

current_timezone = "America/Los_Angeles"
output_json = '{ "solrobjects": [ '  

activityTranslation = {"HKWorkoutActivityTypeRunning": "running",
                       'HKWorkoutActivityTypeElliptical':  "elliptical",
                       'HKWorkoutActivityTypeWalking': "walking",
                       'HKWorkoutActivityTypeYoga': "yoga",
                       'HKWorkoutActivityTypeFunctionalStrengthTraining': "weight lifting",
                       'HKWorkoutActivityTypeRowing': "rowing"}

type_count = {}
tree = ET.parse(input_data_path)
root = tree.getroot()
count = 0

for child in root:
    details = { "indoor": False}
    if child.tag == "Workout":
        textDescription = ""
        count = count +1
#        print("COUNT = ")
#        print(count)
        if count > 10000:
            break
        if "workoutActivityType" in child.attrib:
#            print (child.attrib)
            if child.attrib["workoutActivityType"] in activityTranslation:
                wtype = "base:" + activityTranslation[child.attrib["workoutActivityType"]]
                #textDescription = activityTranslation[child.attrib["workoutActivityType"]]
                details["activity"] = activityTranslation[child.attrib["workoutActivityType"]]
            else:
                wtype = "base/" + child.attrib["workoutActivityType"]
                textDescription = child.attrib["workoutActivityType"]

        if  child.attrib["workoutActivityType"] in type_count:
            type_count[child.attrib["workoutActivityType"]] = type_count[child.attrib["workoutActivityType"]] + 1
        else:
            type_count[child.attrib["workoutActivityType"]] = 1
        start = child.attrib["startDate"]
        experienced_startTime = convertToTimezone (start,ORIGIN_TIMEZONE, current_timezone)
        details["start"] = extractTOD(experienced_startTime)[0:5]
        
        obj = LLEntry(wtype, experienced_startTime, SOURCE)
        #print (start)
       
        #print (obj.startTimeOfDay)
        if "endDate" in child.attrib:
            obj.endTime = child.attrib["endDate"]
            
        else:
            print ("no end date")

        if "duration" in child.attrib:
            obj.duration = child.attrib["duration"]
            #textDescription = textDescription +  obj.duration + " minutes;"
            details["duration"] = child.attrib["duration"]
        if "totalDistance" in child.attrib:

            obj.distance = child.attrib["totalDistance"]
            details["distance"] = child.attrib["totalDistance"]
            #textDescription = textDescription  + obj.distance + " miles"
        if "totalEnergyBurned" in child.attrib:
            obj.calories = child.attrib["totalEnergyBurned"]
            # textDescription = textDescription + " calories " + obj.calories
               
               
        for item in child.findall('MetadataEntry'):
#            print (item.attrib["key"])
            if (item.attrib["key"]) == "HKIndoorWorkout":
                obj.outdoor = item.attrib["value"]
                # textDescription = textDescription + " indoor= " + item.attrib["value"]
                details["indoor"] = item.attrib["value"]
            if (item.attrib["key"]) == "HKTimeZone":
#                print (item.attrib["value"])
                textDescription = textDescription + " timezone: " + item.attrib["value"]
                obj.timezone = item.attrib["value"]
                if obj.timezone != current_timezone:
#                    print ("changing current time zone to: ", obj.timezone)
                    current_timezone = obj.timezone
            if (item.attrib["key"]) == "HKWeatherTemperature":
                obj.temperature = item.attrib["value"] 

        obj.textDescription = generate_textDescription(details)
        print("Text description: ", obj.textDescription)
        

        experienced_endTime = convertToTimezone (obj.endTime,ORIGIN_TIMEZONE, current_timezone)
        obj.startTimeOfDay = extractTOD(experienced_startTime)
        obj.endTimeOfDay = extractTOD(obj.endTime)
        if count > 1:
            output_json = output_json + " , "
        output_json = output_json + obj.toJson()

output_json = output_json + " ] } "     
#print (output_json)

print (type_count)

with open(OUTPUT_FILE, 'w') as outfile:
    outfile.write(output_json)          
       


