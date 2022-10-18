import json
import os
from pathlib import Path

from src.objects.LLEntry_inverted_index import LLEntryInvertedIndex
from src.objects.LLEntry_obj import LLEntry
from src.persistence.personal_data_db import PersonalDataDBConnector
from src.persistence.photo_data_db import PhotoDataDB
import pickle

# This is where the photos and their jsons sit

DATA_DIR = str(Path("data").absolute())
OUTPUT_FILE = "date_inverted_index.json"
GTIMELINE_DIR = "2019"
INPUT_FILES = {"google_timeline_data.json", "applehealth_data.json", "spotify.json",  "amazon_purchases.json" }
output_path = DATA_DIR +"/"+ OUTPUT_FILE

inverted_index = LLEntryInvertedIndex()
count = 0

print("Index created from files. ")
print("Creating Index from DB... ")
#Photos are extracted from DB
db = PhotoDataDB()
result_cursor = db.search_photos("enriched_data", {"export_done": "=1"})
for row in result_cursor:
    enriched_entry:LLEntry = pickle.loads(row[0])
    count += 1
    date = enriched_entry.startTime[0:10]
    inverted_index.addEntry(date, row[0])
photos_count=count
print("Photos count:", photos_count)

pddb = PersonalDataDBConnector()
result_cursor = pddb.search_personal_data("data")
for row in result_cursor:
    data:LLEntry = pickle.loads(row[0])
    count += 1
    date = data.startTime[0:10]
    inverted_index.addEntry(date, row[0])
print("Non-Photo count:", count - photos_count)
output_obj = pickle.dumps(inverted_index)
print ("count and number of keys are: ", count, " and ", len(inverted_index.index.keys()))
print ("Keys: ", sorted(inverted_index.index.keys()))
outfile = open(output_path, 'wb')
pickle.dump(inverted_index,outfile)
