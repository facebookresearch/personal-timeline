import json
import os
from pathlib import Path
from src.objects.LLEntry_obj import LLEntry
from src.persistence.photo_data_db import PhotoDataDB
import pickle

# This is where the photos and their jsons sit

DATA_DIR = str(Path("data").absolute())
OUTPUT_FILE = "date_inverted_index.json"
GTIMELINE_DIR = "2019"
INPUT_FILES = {"google_timeline_data.json", "applehealth_data.json", "spotify.json",  "amazon_purchases.json" }
output_path = DATA_DIR +"/"+ OUTPUT_FILE

index = {}
count = 0
for f in INPUT_FILES:
    path = DATA_DIR + f
    if not os.path.exists(path):
        print ("Could not find " + path)
        continue 
    print("Reading: ", path)
    with open(path, 'r') as f1:
        r1 = f1.read()
        data = json.loads(r1)
        objs = data["solrobjects"]
        for obj in objs:
            count = count + 1
            date = obj["startTime"][0:10]
            if date in index:
                index[date].append(obj)
            else:
                index[date] = [ obj ]

print("Index created from files. ")
print("Creating Index from DB... ")
#Photos are extracted from DB
db = PhotoDataDB()
result_cursor = db.search_photos("enriched_data", {"export_done": "=1"})
for row in result_cursor:
    enriched_entry:LLEntry = pickle.loads(row[0])
    count = count + 1
    date = enriched_entry.startTime[0:10]
    if date in index:
        index[date].append(enriched_entry.toJson())
    else:
        index[date] = [enriched_entry.toJson()]

output_json = json.dumps(index)
print ("count and number of keys are: ", count, " and ", len(index.keys()))
print ("Keys: ", sorted(index.keys()))
with open(output_path, 'w') as outfile:
    outfile.write(output_json)
