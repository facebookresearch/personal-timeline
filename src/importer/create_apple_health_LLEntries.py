from pathlib import Path

from tqdm import tqdm

from src.importer.all_importers import GenericImporter
from src.objects.EntryTypes import EntryType
from src.objects.LLEntry_obj import LLEntry
import xml.etree.ElementTree as ET

from src.objects.import_configs import SourceConfigs
from src.util import *

APPLE_INPUT_DATA_FILE = "iwatch.xml"
OUTPUT_FILE = "applehealth_data.json"
SOURCE = "AppleHealth"
TYPE = "base/"
ORIGIN_TIMEZONE = "America/Los_Angeles"


class AppleHealthImporter(GenericImporter):
    def __init__(self, source_id:int, source_name: str, entry_type: EntryType, configs:SourceConfigs):
        print("AppleHealthImporter")
        self.current_timezone = "America/Los_Angeles"
        self.activityTranslation = {"HKWorkoutActivityTypeRunning": "running",
                               'HKWorkoutActivityTypeElliptical': "elliptical",
                               'HKWorkoutActivityTypeWalking': "walking",
                               'HKWorkoutActivityTypeYoga': "yoga",
                               'HKWorkoutActivityTypeFunctionalStrengthTraining': "weight lifting",
                               'HKWorkoutActivityTypeRowing': "rowing"}
        super().__init__(source_id, source_name, entry_type, configs)

    def generate_textDescription(self, details):
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

    def import_data(self, field_mappings):
        dir_path = str(Path(self.configs.input_directory).absolute())
        print("Reading", dir_path)
        entries = self.get_type_files_deep(dir_path,
                                           self.configs.filename_regex,
                                           self.configs.filetype.split(","))
        if len(entries) == 0:
            print("NotFound: Data expected in ", self.configs.input_directory, " while importing for ",
                  self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:", self.configs.filetype)
            return
        for entry in tqdm(entries):
            print("Reading File: ", entry)
            tree = ET.parse(entry)
            root = tree.getroot()
            count=0
            for child in tqdm(root):
                obj = self.create_LLEntry(child)
                if obj is not None:
                    # Write Obj to personal-data
                    data_entry = self.build_db_entry(obj)
                    self.pdc.add_or_replace_personal_data(data_entry, "dedup_key")
                    count += 1
            print("Count:", count)

    def create_LLEntry(self, child):
        type_count = {}
        details = { "indoor": False}
        if child.tag == "Workout":
            textDescription = ""
            if "workoutActivityType" in child.attrib:
                # print("child.attrib",child.attrib)
                if child.attrib["workoutActivityType"] in self.activityTranslation:
                    wtype = "base:" + self.activityTranslation[child.attrib["workoutActivityType"]]
                    #textDescription = activityTranslation[child.attrib["workoutActivityType"]]
                    details["activity"] = self.activityTranslation[child.attrib["workoutActivityType"]]
                else:
                    wtype = "base/" + child.attrib["workoutActivityType"]
                    textDescription = child.attrib["workoutActivityType"]

            if  child.attrib["workoutActivityType"] in type_count:
                type_count[child.attrib["workoutActivityType"]] = type_count[child.attrib["workoutActivityType"]] + 1
            else:
                type_count[child.attrib["workoutActivityType"]] = 1
            start = child.attrib["startDate"]
            experienced_startTime = convertToTimezone (start,ORIGIN_TIMEZONE, self.current_timezone)
            details["start"] = extractTOD(experienced_startTime)[0:5]

            obj = LLEntry(wtype, experienced_startTime, SOURCE)
            #print (start)

            # print ("startTimeOfDay",obj.startTimeOfDay)
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
                # print (item.attrib["key"])
                if (item.attrib["key"]) == "HKIndoorWorkout":
                    obj.outdoor = item.attrib["value"]
                    # textDescription = textDescription + " indoor= " + item.attrib["value"]
                    details["indoor"] = item.attrib["value"]
                if (item.attrib["key"]) == "HKTimeZone":
                    # print (item.attrib["value"])
                    textDescription = textDescription + " timezone: " + item.attrib["value"]
                    obj.timezone = item.attrib["value"]
                    if obj.timezone != self.current_timezone:
                        # print ("changing current time zone to: ", obj.timezone)
                        self.current_timezone = obj.timezone
                if (item.attrib["key"]) == "HKWeatherTemperature":
                    obj.temperature = item.attrib["value"]

            obj.textDescription = self.generate_textDescription(details)
            #print("Text description: ", obj.textDescription)
            experienced_endTime = convertToTimezone (obj.endTime,ORIGIN_TIMEZONE, self.current_timezone)
            obj.startTimeOfDay = extractTOD(experienced_startTime)
            obj.endTimeOfDay = extractTOD(obj.endTime)
            return obj
        # else:
        #     print("Child tag",child,"is not workout. Skipping")
        return None



