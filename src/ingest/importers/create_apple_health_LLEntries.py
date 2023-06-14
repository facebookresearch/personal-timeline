# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
from tqdm import tqdm

from src.ingest.importers.generic_importer import GenericImporter
from src.common.objects.EntryTypes import EntryType
from src.common.objects.LLEntry_obj import LLEntry
import xml.etree.ElementTree as ET

from src.common.objects.import_configs import SourceConfigs
from src.common.util import *

APPLE_INPUT_DATA_FILE = "iwatch.xml"
OUTPUT_FILE = "applehealth_data.json"
SOURCE = "AppleHealth"
TYPE = "base/"
ORIGIN_TIMEZONE = "America/Los_Angeles"


class AppleHealthImporter(GenericImporter):
    def __init__(self, source_id:int, source_name: str, entry_type: EntryType, configs:SourceConfigs):
        # print("AppleHealthImporter")
        self.current_timezone = "America/Los_Angeles"
        self.activityTranslation = {"HKWorkoutActivityTypeRunning": "running",
                               'HKWorkoutActivityTypeElliptical': "elliptical",
                               'HKWorkoutActivityTypeWalking': "walking",
                               'HKWorkoutActivityTypeYoga': "yoga",
                               'HKWorkoutActivityTypeFunctionalStrengthTraining': "weight lifting",
                               'HKWorkoutActivityTypeRowing': "rowing"}
        super().__init__(source_id, source_name, entry_type, configs)

    def import_data(self, field_mappings):
        dir_path = str(Path(self.configs.input_directory).absolute())
        print("Reading", dir_path)
        entries = self.get_type_files_deep(dir_path,
                                           self.configs.filename_regex,
                                           self.configs.filetype.split(","))
        print(f"Entries: {entries}")
        if entries is None or len(entries) == 0:
            print("NotFound: Data expected in ", self.configs.input_directory, " while importing for ",
                  self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:", self.configs.filetype)
            return

        count = 0
        tag = "Workout"
        for entry in tqdm(entries):
            print(f"Reading entry File: {entry}\n")
            for child in self.parse_large_xml_file(entry):
                obj = self.create_LLEntry(child, tag)
                if obj is not None:
                    # Write Obj to personal-data
                    data_entry = self.build_db_entry(obj)
                    self.pdc.add_or_replace_personal_data(data_entry, "dedup_key")
                    # print(f"Written to DB. DedupKey: {data_entry['dedup_key']}")
                    count += 1
            print("Count:", count)

    def parse_large_xml_file(self, xml_file_path):
        """
        Parses a large XML file in a memory-efficient manner using ElementTree.
        """
        context = ET.iterparse(xml_file_path, events=("start", "end"))
        element_stack = []
        for event, child in context:
            if event == 'start':
                element_stack.append(child)
            if event == "end":
                element_stack.pop()
                yield child
                if element_stack:
                    element_stack[-1].remove(child)

    def create_LLEntry(self, child, tag):
        type_count = {}
        details = { "indoor": False}
        if child.tag == tag:
            text_description = ""
            if "workoutActivityType" in child.attrib:
                if child.attrib["workoutActivityType"] in self.activityTranslation:
                    wtype = "base:" + self.activityTranslation[child.attrib["workoutActivityType"]]
                    details["activity"] = self.activityTranslation[child.attrib["workoutActivityType"]]
                else:
                    wtype = "base/" + child.attrib["workoutActivityType"]
                    text_description = child.attrib["workoutActivityType"]

            if child.attrib["workoutActivityType"] in type_count:
                type_count[child.attrib["workoutActivityType"]] = type_count[child.attrib["workoutActivityType"]] + 1
            else:
                type_count[child.attrib["workoutActivityType"]] = 1
            start = child.attrib["startDate"]
            experienced_start_time = convertToTimezone (start,ORIGIN_TIMEZONE, self.current_timezone)
            details["start"] = extractTOD(experienced_start_time)[0:5]

            obj = LLEntry(wtype, experienced_start_time, SOURCE)

            if "endDate" in child.attrib:
                obj.endTime = child.attrib["endDate"]
            else:
                print ("no end date")

            if "duration" in child.attrib:
                obj.duration = child.attrib["duration"]
                details["duration"] = child.attrib["duration"]
            if "totalDistance" in child.attrib:

                obj.distance = child.attrib["totalDistance"]
                details["distance"] = child.attrib["totalDistance"]
            if "totalEnergyBurned" in child.attrib:
                obj.calories = child.attrib["totalEnergyBurned"]

            for item in child.findall('MetadataEntry'):
                if (item.attrib["key"]) == "HKIndoorWorkout":
                    obj.outdoor = item.attrib["value"]
                    details["indoor"] = item.attrib["value"]
                if (item.attrib["key"]) == "HKTimeZone":
                    text_description = text_description + " timezone: " + item.attrib["value"]
                    obj.timezone = item.attrib["value"]
                    if obj.timezone != self.current_timezone:
                        self.current_timezone = obj.timezone
                if (item.attrib["key"]) == "HKWeatherTemperature":
                    obj.temperature = item.attrib["value"]

            obj.textDescription = self.generate_textDescription(details)
            obj.startTimeOfDay = extractTOD(experienced_start_time)
            obj.endTimeOfDay = extractTOD(obj.endTime)
            return obj
        else:
            return None



