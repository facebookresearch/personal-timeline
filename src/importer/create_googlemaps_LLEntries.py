import json
from pathlib import Path

from tqdm import tqdm

from src.importer.all_importers import GenericImporter
from src.objects.EntryTypes import EntryType
from src.objects.LLEntry_obj import LLEntry
from src.objects.import_configs import SourceConfigs
from src.util import *
import time
from geopy.geocoders import Nominatim

# This is where the photos and their jsons sit
ORIGIN_TIMEZONE = str(pytz.utc)
global geolocator
geolocator = Nominatim(user_agent="pim_photo")


# se: True if it's for start, False for end
# lat/long are strings

class GoogleMapsImporter(GenericImporter):
    def __init__(self, source_id:int,  source_name: str, entry_type: EntryType, configs:SourceConfigs):
        super().__init__(source_id, source_name, entry_type, configs)
    def calculateLocationFromLatLong(self, lat, lon):
        # print ("lat is ", lat)
        time.sleep(1)
        location = geolocator.reverse(str(lat) + "," + str(lon), addressdetails=True)
        return (location)

    def generate_textDescription(self, details):
        # print (details)
        result = details["start"] + ": "
        if "activity" not in details:
            return (result + "unidentified activity")
        result = result + details["activity"] + " "
        if "duration" in details:
            result = result + truncateStringNum(details["duration"], 0) + " minutes "
        if "distance" in details:
            distanceNum = truncateStringNum(details["distance"], 2)
            if distanceNum != "0.0":
                result = result + distanceNum + " miles "
        # if details["indoor"] != "0":

    #        result = result + "(indoors)"

    def placeVisitExtract(self, visit):
        # print ("in place visit extract")
        start = visit["duration"]["startTimestamp"][0:19]
        start_lat = visit["location"]["latitudeE7"]
        start_lon = visit["location"]["longitudeE7"]
        target_timezone = convertlatlongToTimezone(start_lat, start_lon)
        experienced_start_time = convertToTimezone(start, ORIGIN_TIMEZONE, target_timezone)

        # print("visit: lat long, start, target_timezone, experiencedStartTime")
        # print(convertOutOfE7(start_lat))
        # print(convertOutOfE7(start_lon))
        # print(start)
        # print(target_timezone)
        # print(experienced_start_time)

        obj = LLEntry(self.entry_type, experienced_start_time, self.source_name)
        obj.lat_lon.append({"lat": convertOutOfE7(start_lat),
                            "lon": convertOutOfE7(start_lon)})
        startTOD = experienced_start_time[11:19]
        obj.startTimeOfDay = startTOD
        textDescription = startTOD[0:5] + ": "
        if "location" in visit:
            #Keep placeholder to be replaced after geo enrichment
            textDescription = textDescription + "visit to $location"

        if "duration" in visit:
            obj.endTime = visit["duration"]["endTimestamp"][0:19]
            experienced_endTime = convertToTimezone(visit["duration"]["endTimestamp"][0:19],
                                                    ORIGIN_TIMEZONE, target_timezone)
            obj.endTime = experienced_endTime
            obj.endTimeOfDay = experienced_endTime[11:19]

            tstart = datetime.fromisoformat(obj.startTime)
            tend = datetime.fromisoformat(obj.endTime)
            dur = tend - tstart
            obj.duration = str(dur)
            textDescription = textDescription + " (duration: " + obj.duration + ")"

        obj.textDescription = textDescription
        # print("TEXT DESCRIPTION:  ", obj.textDescription)
        return obj

    def activitySegmentExtract(self, activity):
        # print("in activity extract")
        translation = {"IN_PASSENGER_VEHICLE": "drive",
                       "WALKING": "walk",
                       "MOTORCYCLING": "motorcycle", "IN_BUS": "bus",
                       "IN_SUBWAY": "subway", "CYCLING": "cycling",
                       "FLYING": "fly"}
        # if "activityType" not in activity:
        #     print("activityType not in Activity")
        #     print(activity)
        textActivity = ""
        wtype = self.entry_type
        if "activityType" in activity:
            if activity["activityType"] in translation:
                wtype = "base:" + translation[activity["activityType"]]
                textActivity = translation[activity["activityType"]]
            else:
                wtype = "base:" + activity["activityType"]
                textActivity = "Unrecognized activity"
                print("add new activity type to dictionary ", activity["activityType"])

        start = activity["duration"]["startTimestamp"][0:19]

        if "latitudeE7" not in activity["startLocation"] or \
            "longitudeE7" not in activity["startLocation"] or \
            "latitudeE7" not in activity["endLocation"] is None or \
            "longitudeE7" not in activity["endLocation"] is None:
            print("Some Location data is missing. Skipping", activity)
            return

        start_lat = convertOutOfE7(activity["startLocation"]["latitudeE7"])
        start_lon = convertOutOfE7(activity["startLocation"]["longitudeE7"])
        end_lat = convertOutOfE7(activity["endLocation"]["latitudeE7"])
        end_lon = convertOutOfE7(activity["endLocation"]["longitudeE7"])

        target_timezone = convertlatlongToTimezone(activity["startLocation"]["latitudeE7"], \
                                                   activity["startLocation"]["longitudeE7"])
        experienced_startTime = convertToTimezone(start, ORIGIN_TIMEZONE, target_timezone)
        # print("activity: lat long, start, target_timezone, experiencedStartTime")
        # print(start_lat)
        # print(start_lon)
        # print(start)
        # print(target_timezone)
        # print(experienced_startTime)

        startTOD = experienced_startTime[11:19]
        textDescription = startTOD[0:5] + ": " + textActivity
        obj = LLEntry(wtype, experienced_startTime, self.source_name)
        obj.lat_lon.append({"lat": start_lat,
                            "lon": start_lon})
        obj.lat_lon.append({"lat": end_lat,
                            "lon": end_lon})
        obj.startTimeOfDay = startTOD
        experienced_endTime = convertToTimezone(activity["duration"]["endTimestamp"][0:19], ORIGIN_TIMEZONE,
                                                target_timezone)
        obj.endTime = experienced_endTime
        obj.endTimeOfDay = experienced_endTime[11:19]

        tstart = datetime.fromisoformat(obj.startTime)
        tend = datetime.fromisoformat(obj.endTime)
        dur = tend - tstart
        obj.duration = str(dur)
        textDescription = textDescription + " (duration: " + obj.duration + ")"

        if "name" in activity["endLocation"]:
            # print(activity["endLocation"]["name"])
            obj.endLocation = activity["endLocation"]["name"]
            textDescription = textDescription + " ended at " + obj.endLocation
        if "distanceMeters" in activity:
            obj.distance = activity["distanceMeters"]
            textDescription = textDescription + " distance: " + obj.distance

        obj.textDescription = textDescription
        #print("TEXT DESCRIPTION:  ", obj.textDescription)
        return obj


    def import_data(self, field_mappings:list):
        print("Looking for files in", str(Path(self.configs.input_directory).absolute()))
        entries = self.get_type_files_deep(str(Path(self.configs.input_directory).absolute()),
                                           self.configs.filename_regex,
                                           self.configs.filetype.split(","))
        if entries == None or len(entries) == 0:
            print("NotFound: Data expected in", self.configs.input_directory, "while importing for",
                  self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:", self.configs.filetype)
            return

        for entry in tqdm(entries):
            print("Reading File:", entry)
            with open(entry, 'r') as f_json:
                r = f_json.read()
                data = json.loads(r)

            for i in data['timelineObjects']:
                obj = None
                key_list = [*i.keys()]
                if key_list[0] == "placeVisit":
                    obj = self.placeVisitExtract(i["placeVisit"])
                elif key_list[0] == "activitySegment":
                    obj = self.activitySegmentExtract(i["activitySegment"])
                else:
                    print("Can't recognize key", key_list[0])
                if obj is None:
                    # print("Skipping row:", i)
                    continue
                data_entry = self.build_db_entry(obj)
                self.pdc.add_or_replace_personal_data(data_entry, "dedup_key")

