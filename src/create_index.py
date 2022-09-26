import json
import os
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from json_obj import LLEntry

# This is where the photos and their jsons sit

DATA_DIR = "/Users/ayh/Documents/src/pim/src/pim-photos/data/"
OUTPUT_FILE = DATA_DIR + "date_inverted_index.json"
GTIMELINE_DIR = "2019"
cwd = Path()
INPUT_FILES = {"google_timeline_data.json", "photo_data.json", "applehealth_data.json", "spotify.json",  "amazon_purchases.json" }


index = {}

output_path = DATA_DIR + OUTPUT_FILE

count = 0
for f in INPUT_FILES:
    
    path = DATA_DIR + f
    if not os.path.exists(path):
        print ("Could not find " + path)
        continue 

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

output_json = json.dumps(index)
print ("count and number of keys are ")
print(count)
print (len(index.keys()))
print (sorted(index.keys()))
with open(OUTPUT_FILE, 'w') as outfile:
    outfile.write(output_json)
