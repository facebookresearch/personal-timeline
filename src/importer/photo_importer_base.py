import os
from pathlib import Path
import re
import pytz
from parsedatetime import parsedatetime
from timezonefinder import TimezoneFinder
import datetime
from datetime import datetime
from abc import abstractmethod
from src.objects.EntryTypes import EntryType
from src.objects.LLEntry_obj import LLEntry
from PIL import Image
from pillow_heif import register_heif_opener

from src.objects.import_configs import SourceConfigs

register_heif_opener()

from src.persistence.personal_data_db import PersonalDataDBConnector

class PhotoImporter:
    @abstractmethod
    def __init__(self, source_id:int, source_name:str, entry_type:EntryType, configs:SourceConfigs):
        self.pdc = PersonalDataDBConnector()
        self.source_id = source_id
        self.source_name = source_name
        self.entry_type = entry_type
        self.configs = configs
        self.cal = parsedatetime.Calendar()

    @abstractmethod
    def import_photos(self, cwd, subdir):
        pass

    def import_data(self, field_mappings:list):
        print("Import Data for", self.source_name)
        cwd = str(Path(self.configs.input_directory).absolute())
        self.import_photos(cwd, None)

    def calculateExperiencedTimeRealAndUtc(self, latitude: float, longitude: float, timestamp: int):
        # get timestamp
        utc = pytz.utc
        utc_dt = utc.localize(datetime.utcfromtimestamp(timestamp))
        # translate lat/long to timezone
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        # print(timezonetf)
        real_timezone = pytz.timezone(timezone_str)
        real_date = real_timezone.normalize(utc_dt.astimezone(real_timezone))
        #print("converted into: ", real_date)
        return str(real_date), str(utc_dt)

    def get_type_files_deep(self, pathname: str, filename_pattern: str, type: list) -> list:
        json_files = []
        type_str: str = "|".join(type).lower()
        if filename_pattern is None:
            filename_regex = ".*"
        else:
            filename_regex = ".*" + filename_pattern.lower() + ".*"
        if os.path.isdir(pathname):
            dir_entries = os.listdir(pathname)
            for dir_entry in dir_entries:
                all_json = self.get_type_files_deep(pathname + "/" + dir_entry, filename_pattern, type)
                if all_json is not None:
                    if isinstance(all_json, list):
                        for one_json in all_json:
                            json_files.append(one_json)
                    else:
                        json_files.append(all_json)
            return json_files
        elif os.path.isfile(pathname):
            if re.match(filename_regex + "\.(" + type_str + ")$", pathname.lower()):
                path_arr = []
                path_arr.append(pathname)
                return path_arr

    # Given a nested json(haystack), this function finds all occurrences
    # of the key(needle) and returns a list of found entries
    def find_all_in_haystack(self, needle, haystack, return_parent: bool):
        if isinstance(haystack, dict) and needle in haystack.keys():
            if return_parent:
                # print("FOUND:::", haystack)
                return haystack
            else:
                # print("FOUND:::", haystack[needle])
                return haystack[needle]
        else:
            found_elements = []
            if isinstance(haystack, dict):
                for hay in haystack:
                    # print(haystack[hay], "type: ", type(haystack[hay]))
                    out = self.find_all_in_haystack(needle, haystack[hay], return_parent)
                    if out is not None:
                        found_elements.append(out)
            elif isinstance(haystack, list):
                for hay in haystack:
                    # print(hay, "type: ", type(hay))
                    out = self.find_all_in_haystack(needle, hay, return_parent)
                    if out is not None:
                        found_elements.append(out)
            #print("Found Elements: ", found_elements)
            # TODO: Some hacky cleanup. Sure there's a better way to create a non-nested list
            found_elements = list(filter(None, found_elements))
            return list(self.flatten(found_elements))

    # Function to flatten a nested list of lists recursively
    def flatten(self, struct):
        for i in struct:
            if isinstance(i, (list, tuple)):
                for j in self.flatten(i):
                    yield j
            else:
                yield i

    # Extracts just the name of the file along with the extension
    # give full path to the file
    def get_filename_from_path(self, uri):
        uri_arr = uri.split("/")
        return uri_arr[len(uri_arr) - 1]


    def is_photo_already_processed(self, filename, taken_timestamp):
        return self.pdc.is_same_photo_present(self.source_id, filename, taken_timestamp)

    def create_LLEntry(self,
                       uri,
                       latitude,
                       longitude,
                       taken_timestamp,
                       tagged_people,
                       imageViews=0) -> LLEntry:
        real_start_time, utc_start_time = self.calculateExperiencedTimeRealAndUtc(latitude,
                                                                        longitude, taken_timestamp)
        # TODO:Photo Location would be an enrichment step.

        obj = LLEntry(self.entry_type, real_start_time, self.source_name)
        obj.startTimeOfDay = real_start_time[11:19]
        obj.lat_lon.append({"lat":latitude, "lon":longitude})

        #Specific to Image
        obj.imageFilePath = uri
        obj.imageFileName = self.get_filename_from_path(uri)
        obj.imageTimestamp = taken_timestamp
        obj.peopleInImage = tagged_people
        #TODO: Get more details from image
        im = Image.open(uri)
        width, height = im.size
        obj.imageWidth = width
        obj.imageHeight = height
        return obj