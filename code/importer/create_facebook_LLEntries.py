import json
import os
from pathlib import Path
from PIL import Image
from code.objects.LLEntry_obj import LLEntry
from code.enrichment.location_time_enrichment import LocationTimeEnricher
import re

# This is where the photos and their jsons sit
PHOTO_DIRECTORY = "photos"

OUTPUT_FILE = "photo_data.json"
# This is where the photos and their jsons sit
FB_POSTS_DIR = ["posts/album"]
SOURCE = "Facebook Posts"
TYPE = "base/photo"

# This is where the intermediate json files sit
ROOT_DIRECTORY = "~/Documents/code/pim/"

def get_type_files_deep(pathname, type):
    json_files = []
    if os.path.isdir(pathname):
        dir_entries = os.listdir(pathname)
        for dir_entry in dir_entries:
            all_json = get_type_files_deep(pathname + "/" + dir_entry, type)
            if all_json is not None:
                if isinstance(all_json, list):
                    for one_json in all_json:
                        json_files.append(one_json)
                else:
                    json_files.append(all_json)
        return json_files
    elif os.path.isfile(pathname) and re.match(".*\." + type, pathname):
        return pathname


def find_all_in_haystack(needle, haystack, return_parent: bool):
    if isinstance(haystack, dict) and needle in haystack.keys():
        if (return_parent):
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
                out = find_all_in_haystack(needle, haystack[hay], return_parent)
                if out is not None:
                    found_elements.append(out)
        elif isinstance(haystack, list):
            for hay in haystack:
                # print(hay, "type: ", type(hay))
                out = find_all_in_haystack(needle, hay, return_parent)
                if out is not None:
                    found_elements.append(out)
        #print("Found Elements: ", found_elements)
        # TODO: Some hacky cleanup. Sure there's a better way to create a non-nested list
        found_elements = list(filter(None, found_elements))
        return flatten(found_elements)

def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def build_output(json_filepath):
    json_files = get_type_files_deep(json_filepath, "json")
    print("All json files in path: ", json_files)
    output_obj_list = []

    for json_file in json_files:
        print("Reading File: ", json_file)
        with open(json_file, 'r') as f1:
            r = f1.read()
            post_data = json.loads(r)
        #print("post_data is of type: ", type(post_data))
        image_container = find_all_in_haystack("uri", post_data, True)
        #print("Image_Container", image_container)
        for image_data in image_container:
            if isinstance(image_data, dict) and "uri" in image_data.keys():
                uri = image_data["uri"]
                exif_data = find_all_in_haystack("exif_data", image_data, False)
                print("exif_data: ", exif_data)
                if exif_data and isinstance(exif_data, list):
                    latitude:float = float(exif_data[0]["latitude"]) if "latitude" in exif_data[0].keys() else 0.0
                    longitude:float = float(exif_data[0]["longitude"]) if "longitude" in exif_data[0].keys() else 0.0
                    taken_timestamp:int = int(exif_data[0]["taken_timestamp"]) \
                        if "taken_timestamp" in exif_data[0].keys() else 0
                    if latitude==0.0 and longitude==0.0 and taken_timestamp==0:
                        continue
                    real_start_time, utc_start_time = LocationTimeEnricher.calculateExperiencedTimeRealAndUtc(latitude, longitude, taken_timestamp)
                    location = LocationTimeEnricher.calculateLocation(latitude, longitude)
                    print("uri: ", uri)
                    print("latitude:", latitude)
                    print("longitude:", longitude)
                    print("location:", location)
                    print("taken_timestamp:", taken_timestamp)
                    print("real_start_time:", real_start_time)
                    print("utc_start_time:", utc_start_time)


cwd = str(Path(PHOTO_DIRECTORY).absolute())
output_json = json.dumps({})
output_obj_list = []
for dir in FB_POSTS_DIR:
    json_filepath = cwd + "/" + dir
    print("Using path: ", json_filepath)
    output_obj_list.append(build_output(json_filepath))

# output_json["solrobjects"] = output_obj_list
