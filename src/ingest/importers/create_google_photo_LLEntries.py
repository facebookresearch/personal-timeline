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
import sqlite3
from pathlib import Path
from tqdm import tqdm

from src.ingest.importers.photo_importer_base import PhotoImporter
from src.common.objects.EntryTypes import EntryType
from src.common.objects.import_configs import SourceConfigs


class GooglePhotosImporter(PhotoImporter):
    def __init__(self, source_id:int,  source_name: str, entry_type: EntryType, configs:SourceConfigs):
        super().__init__(source_id, source_name, entry_type, configs)

    def import_photos(self, cwd, subdir):
        orphan_json_files = []
        print("Using path: ", str(Path(self.configs.input_directory).absolute()))
        entries = self.get_type_files_deep(str(Path(self.configs.input_directory).absolute()),
                                           None,
                                           self.configs.filetype.split(","))
        if entries is None or len(entries) == 0:
            print("NotFound: Data expected in ", self.configs.input_directory, " while importing for ",
                  self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:", self.configs.filetype)
            return

        for img_file in entries:
            try:
                self.pdc.add_only_photo(self.source_id, self.get_filename_from_path(img_file), img_file)
            except sqlite3.IntegrityError:
                #print(img_file, " already present in DB")
                continue
        total_imported = 0
        heic_counter = 0
        json_entries = self.get_type_files_deep(str(Path(self.configs.input_directory).absolute()),
                                           self.configs.filename_regex,
                                           "json".split(","))
        if json_entries is None or len(json_entries) == 0:
            print("NotFound: Json Data expected in ", self.configs.input_directory, " while importing for ",
                  self.source_name)
            return
        skipped = 0
        # Now that all photos are added, we go through all jsons and add them to DB
        for json_file in tqdm(json_entries):
            #print("Reading File: ", json_file)
            with open(json_file, 'r') as f1:
                r = f1.read()
                content = json.loads(r)
            # some JSON could be empty (i.e print-subscriptions.json)
            if len(content) == 0:
                skipped+=1
                continue
            # some JSON will not contain title (i.e shared_album_comments.json)
            if 'title' not in content.keys():
                skipped += 1
                continue
            imageFileName=content["title"]
            #Search for DB row that has the full imagePath
            select_cols = "id, imageFilePath, data_timestamp"
            where_clause = {"source_id": "=" + str(self.source_id), "imageFileName": "=\"" + imageFileName + "\""}
            res = self.pdc.search_personal_data(select_cols, where_clause)
            db_entry = res.fetchone()
            if db_entry is None:
                orphan_json_files.append(json_file)
                continue
            row_id = db_entry[0]
            imageFilePath = db_entry[1]
            timestamp = db_entry[2]
            if timestamp is not None:
                # print("RowId: ", row_id, " is already processed. Skipping recreation...")
                skipped += 1
                continue
            # get lat/long
            latitude = float(content["geoData"]["latitude"])
            longitude = float(content["geoData"]["longitude"])
            taken_timestamp = int(content["photoTakenTime"]["timestamp"])
            tagged_people=[]
            if "people" in content.keys():
                # print (content["people"])
                tagged_people = content["people"]
            if "imageViews" in content.keys():
                imageViews = content["imageViews"]
            # if os.path.splitext(imageFilePath)[1] == '.HEIC':
            #     heic_counter +=1
                # continue
            obj = self.create_LLEntry(imageFilePath, latitude, longitude, taken_timestamp, tagged_people, imageViews)
            self.pdc.add_or_replace_personal_data({"data": obj, "data_timestamp": int(taken_timestamp), "id": row_id}, "id")
            total_imported += 1
        print("Orphaned Json Files: ", len(orphan_json_files))
        print("Skipped: ", skipped)
        print("Total processed: ", total_imported)
        # print("Total HEIC ignored: ", heic_counter)
        # if heic_counter > 0:
        #     print('Please convert your HEIC file to JPEG')
