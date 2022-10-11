import json
import sqlite3
from time import sleep
from tqdm import tqdm
import os

from src.importer.photo_importer_base import PhotoImporter
from src.objects.EntryTypes import EntryType

# This is where the photos and their jsons sit
INPUT_DIRECTORY = "personal-data/google_photos"
# Google Photos Configs
SOURCE = "Google Photos"
TYPE = EntryType.PHOTO


class GooglePhotosImporter(PhotoImporter):
    def __init__(self):
        super().__init__(INPUT_DIRECTORY, None, SOURCE, TYPE)

    def import_photos(self, cwd, subdir):
        orphan_json_files = []
        json_filepath = cwd + "/" + subdir if subdir is not None else cwd
        print("Using path: ", json_filepath)
        if os.path.isdir(json_filepath):
            # Breaking it down to avoid too many files, just in case
            dir_entries = os.listdir(json_filepath)
            for dir_entry in dir_entries:
                uri = json_filepath +"/"+ dir_entry
                img_files = self.get_type_files_deep(uri, ["jpg", "JPEG", "HEIC"])
                if img_files is None:
                    continue
                for img_file in img_files:
                    try:
                        self.db.add_only_photo(SOURCE, self.get_filename_from_path(img_file), img_file)
                    except sqlite3.IntegrityError:
                        #print(img_file, " already present in DB")
                        continue
            total_imported = 0
            heic_counter = 0
            # Now that all photos are added, we go through all jsons and add them to DB
            for dir_entry in tqdm(dir_entries):
                print("Reading Directory: ", dir_entry)
                uri = json_filepath + "/" + dir_entry
                json_files = self.get_type_files_deep(uri, ["json"])
                #print("Reading json files in path ", uri, ": ", json_files)
                if json_files is None:
                    continue
                for json_file in tqdm(json_files):
                    # print("Reading File: ", json_file)
                    with open(json_file, 'r') as f1:
                        r = f1.read()
                        content = json.loads(r)
                    # some JSON could be empty (i.e print-subscriptions.json)
                    if len(content) == 0:
                        continue
                    # some JSON will not content title (i.e shared_album_comments.json)
                    if 'title' not in content.keys():
                        continue
                    imageFileName=content["title"]
                    #Search for DB row that has the full imagePath
                    select_cols = "id, imageFilePath, timestamp"
                    where_clause = {"source": "=\""+SOURCE+"\"", "imageFileName": "=\""+imageFileName+"\""}
                    res = self.db.search_photos(select_cols, where_clause)
                    db_entry = res.fetchone()
                    if db_entry is None:
                        orphan_json_files.append(json_file)
                        continue
                    row_id = db_entry[0]
                    imageFilePath = db_entry[1]
                    timestamp = db_entry[2]
                    if timestamp is not None:
                        #print("RowId: ", row_id, " is already processed. Skipping recreation...")
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
                    if os.path.splitext(imageFilePath)[1] == '.HEIC':
                        heic_counter +=1
                        continue
                    obj = self.create_LLEntry(imageFilePath, latitude, longitude, taken_timestamp, tagged_people, imageViews)
                    self.db.update_photos(row_id, {"data": obj, "timestamp": int(taken_timestamp)})
                    total_imported += 1
            #print("Orphaned Json Files: ", orphan_json_files)
            print("Total processed: ", total_imported)
            print("Total HEIC ignored: ", heic_counter)
            if heic_counter > 0:
                print('Please convert your HEIC file to JPEG')
        else:
            print(json_filepath, ": No such directory")
