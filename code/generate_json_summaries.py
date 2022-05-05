import PySimpleGUI as sg
import os
import os.path
import json
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from json_obj import LLEntry
from operator import itemgetter
from util import *

ROOT_DIR = "~/Documents/code/pim/"
SUMMARY_FILE = "summaries_index.json"
JSON_SUMMARIES_FILE = "json_summaries_index.json"
DEFAULT_YEAR = "2019"
IMAGE_HEIGHT = 600.0
DEFAULT_IMAGE_WIDTH = 500.0
INITIAL_DATE = "2019-01-01"
json_dir =  Path() / "../data"            
cwd = Path() / ".."

summary_path = json_dir /  SUMMARY_FILE
print (summary_path)

with open(summary_path, 'r') as f2:
    r2 = f2.read()
    data = json.loads(r2)

global summaries
summaries = {}
count = 0
summaries = " [ "
for per in data.keys():
    count = count +1
    if count > 3:
        break
    for element in data[per]:
        print(type(element))
        summaries = summaries + dict_to_json(element)

summaries = result + " ]"
print (summaries)

output_path = cwd / JSON_SUMMARIES_FILE
output_json = json.dumps(dict_to_json(summaries))

