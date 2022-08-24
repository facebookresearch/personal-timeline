import json
import os
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from json_obj import LLEntry
import pytz
from pytz import timezone
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
from util import *
import time
from geopy.geocoders import Nominatim
import pandas as pd
from os.path import exists

#This is the json file with your Spotify streaming history
spotify_streaming_file = "/Users/ayh/Downloads/PIMData/Spotify/StreamingHistory0.json"

OUTPUT_FILE = "spotify.json"
OUTPUT_DIRECTORY = Path() / "../data"
# This is where the intermediate json files sit

SOURCE = "Spotify"

DEFAULT_TOD_FOR_PURCHASES = " 11:00:00"



def streamExtract(endDate, artist, track, msPlayed):
    wtype = "base:streaming"
    experienced_startTime = subtractListeningTime(endDate, msPlayed)
    obj = LLEntry(wtype, experienced_startTime, SOURCE)
    obj.startTimeOfDay = experienced_startTime[11:19]
    obj.textDescription = "Listened to " + artist + " " + track
    obj.endTime = endDate
    return obj


#Spotify specifies the end time of the streaming and the duration, so the start time needs to be calculated. 
def subtractListeningTime(date, ms):
    y, m, d, h, m1 = extractYMDHM(date)
    dd = datetime(y, m, d, h, m1)
    nd = dd - timedelta(seconds=ms/1000.0)
    return (str(nd)[0:19])

def slash_to_dash(date):
    return date[6:10] + "-" + date[3:5] + "-" + date[0:2]

output_json = '{ "solrobjects": [ '  
output_path = OUTPUT_DIRECTORY / OUTPUT_FILE



print("input spotify path is " + spotify_streaming_file)
print("output path is " + str(output_path))

count = 0

if not os.path.exists(spotify_streaming_file):
    print ("Could not find Spotify streaming file ", spotify_streaming_file)
else: 
    with open(spotify_streaming_file, 'r') as f_json:
        r = f_json.read()
        data = json.loads(r)
    
#except IOError:
#    print('Could not find Spotify streaming history file.')
#else:


        for rec in data:
            count = count + 1
            if count < 10: 
                print (rec["endTime"], rec["artistName"], rec["trackName"])
            if count > 1:
                output_json = output_json + " , "
                
            output_json = output_json + streamExtract(rec["endTime"], rec["artistName"], rec["trackName"], rec["msPlayed"]).toJson()
   
    print ("Number of spotify records is: ")
    print (count )
    output_json = output_json + " ] } "
    with open(output_path, 'w') as outfile:
        outfile.write(output_json)

            

    

     
