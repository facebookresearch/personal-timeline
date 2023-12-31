# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import json
from tqdm import tqdm

from src.ingest.importers.photo_importer_base import PhotoImporter
from src.common.objects.EntryTypes import EntryType
from src.common.objects.import_configs import SourceConfigs


class FacebookPhotosImporter(PhotoImporter):
    def __init__(self, source_id:int,  source_name: str, entry_type: EntryType, configs:SourceConfigs):
        super().__init__(source_id, source_name, entry_type, configs)

    def import_photos(self, cwd, subdir):
        json_filepath = cwd + "/" + subdir if subdir is not None else cwd
        print("Using path: ", json_filepath)
        json_files = self.get_type_files_deep(json_filepath,
                                              self.configs.filename_regex,
                                              self.configs.filetype.split(","))
        print("All json files in path: ", json_files)
        for json_file in tqdm(json_files):
            print("Reading File: ", json_file)
            with open(json_file, 'r') as f1:
                r = f1.read()
                post_data = json.loads(r)
            #print("post_data is of type: ", type(post_data))
            #Object boundary in FB jsons are at timestamp or creation_timestamp based on post type
            all_media = self.find_all_in_haystack("timestamp", post_data, True)
            ts2 = self.find_all_in_haystack("creation_timestamp", post_data, True)
            all_media += ts2
            #print("Image_Container", all_media)
            for media_container in tqdm(all_media):
                tagged_people = []
                if isinstance(media_container, dict) and "tags" in media_container.keys():
                    #print("Found tags: ", media_container["tags"])
                    tagged_people = media_container["tags"]
                uri_container = self.find_all_in_haystack("uri", media_container, True)
                count = 0;
                for one_media in tqdm(uri_container):
                    if isinstance(one_media, dict) and "uri" in one_media.keys():
                        count += 1
                        uri = cwd +"/"+ one_media["uri"]
                        exif_data = self.find_all_in_haystack("exif_data", one_media, False)
                        #print("exif_data: ", exif_data)
                        if exif_data and isinstance(exif_data, list):
                            latitude:float = float(exif_data[0]["latitude"]) if "latitude" in exif_data[0].keys() else 0.0
                            longitude:float = float(exif_data[0]["longitude"]) if "longitude" in exif_data[0].keys() else 0.0
                            taken_timestamp:int = int(exif_data[0]["taken_timestamp"]) \
                                if "taken_timestamp" in exif_data[0].keys() else 0
                            if not self.is_photo_already_processed(self.get_filename_from_path(uri), taken_timestamp):
                                if latitude==0.0 and longitude==0.0 and taken_timestamp==0:
                                    #print("No GPS or Time info, skipping: ", self.get_filename_from_path(uri))
                                    continue
                                obj = self.create_LLEntry(uri, latitude, longitude, taken_timestamp, tagged_people)
                                self.pdc.add_photo(self.source_id, obj)
                                # print("OBJ: ",obj)
                            else:
                                #print(self.get_filename_from_path(uri), " is already processed. Skipping recreation...")
                                continue