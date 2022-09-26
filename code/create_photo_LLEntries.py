import json
import os
from pathlib import Path
from PIL import Image
import datetime
from datetime import datetime, timedelta
from datetime import timezone
from LLEntry_obj import LLEntry
import pytz
from pytz import timezone
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time 
import pdb

# This is where the photos and their jsons sit
PHOTO_DIRECTORY = "../photos"

OUTPUT_FILE = "photo_data.json"


SOURCE = "Google Photos"
TYPE = "base/photo"
global geolocator
geolocator = Nominatim(user_agent="pim_timeline")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=5)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=5)

# This is where the intermediate json files sit
ROOT_DIRECTORY = "~/Documents/code/pim/"

def calculateLocation(content):
    latitude = float(content["geoData"]["latitude"])
    longitude = float(content["geoData"]["longitude"])
    time.sleep(1)
    # location = geolocator.reverse(str(latitude)+","+str(longitude), addressdetails=True)
    location = reverse(str(latitude)+","+str(longitude), addressdetails=True)

# geolocator = Nominatim(user_agent="application")

# reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

# location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)



    print (str(location))
    return (location)

def calculateExperiencedTime(content):
    result = ""
    print (content["photoTakenTime"]["formatted"])
    # get lat/long
    latitude = float(content["geoData"]["latitude"])
    longitude = float(content["geoData"]["longitude"])
    # get timestamp
    utc = pytz.utc
    timestamp = int(content["photoTakenTime"]["timestamp"])
    utc_dt = utc.localize(datetime.utcfromtimestamp(timestamp))
    # translate lat/long to timezone
    tf = TimezoneFinder()

    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
    # print(timezonetf)
    tzo = tzwhere.tzwhere()

#    if latitude == 0.0 and longitude == 0.0:
#        timezone_str = "America/Los_Angeles"
#    else:
#        timezone_str = tzo.tzNameAt(latitude, longitude) # real coordinates
    print(timezone_str)
    real_timezone = pytz.timezone(timezone_str)
    real_date = real_timezone.normalize(utc_dt.astimezone(real_timezone))
    print ("converted into: ")
    print (real_date)
    return str(real_date)

cwd = Path() # or Path('.')
jsons_filepath = cwd / "../data/photo_filenames.json"
photos_filepath = cwd / PHOTO_DIRECTORY
captions_filepath = cwd / "../data/photo_captions.json"


output_json = '{ "solrobjects": [ '  
output_dir = {}

with open(jsons_filepath, 'r') as f:
  r1 = f.read()
  names = json.loads(r1)

with open(captions_filepath, 'r') as f_caption:
  r_captions = f_caption.read()
  captions  = json.loads(r_captions)

  
count = 0
# for name in names:
for name in names.values():
    count = count +1
    if count > 10000:
        break
    # file_name = name + ".HEIC.json"
    file_name = name + ".json"
    pdb.set_trace()
    print (file_name)
    j_path = photos_filepath / file_name
    with open(j_path, 'r') as f1:
        r2 = f1.read()
        content = json.loads(r2)
        textDescription = ""
        real_start_time = calculateExperiencedTime(content)
        photo_location = calculateLocation(content)
        date = content["photoTakenTime"]["timestamp"]
        date_integer = int(date)
        utc_timezone = pytz.utc
        utc = pytz.utc
        startTime = str(utc.localize(datetime.utcfromtimestamp(date_integer)))
        print (startTime)
#        startTime = str(datetime.fromtimestamp(date_integer, timezone.utc))

        #obj = SolrObj(TYPE, startTime, SOURCE)
        obj = LLEntry(TYPE, real_start_time, SOURCE)
        obj.startTimeOfDay = real_start_time[11:19]
        obj.startLocation = str(photo_location)
        if photo_location is not None: 
            if "country" in photo_location.raw["address"]:
                obj.startCountry = photo_location.raw["address"]["country"]
                print ("country is ", obj.startCountry)
            if "city" in photo_location.raw["address"]:
                obj.startCity = photo_location.raw["address"]["city"]
            if "state" in photo_location.raw["address"]:
                obj.startState = photo_location.raw["address"]["state"]
        textDescription = real_start_time[11:19] + ": " + str(photo_location)
        print(obj.startTimeOfDay)
        if "people" in content.keys():
            # print (content["people"])
            obj.peopleInImage = content["people"]
            textDescription = textDescription + " with "
            for j in content["people"]:
                print (type(j))
                print (j)
                print (j["name"])
                textDescription = textDescription + "\n " + j["name"]

        if "imageViews" in content.keys():
            obj.imageViews = content["imageViews"]
           # textDescription = textDescription + " \n got " + content["imageViews"] + " views"

        if name in captions.keys():
            obj.imageCaptions = captions[name]
            for j in captions[name]:
                
                 textDescription = textDescription + ", " + j
            # print (captions[name])
            
        obj.latitude = content["geoData"]["latitude"]
        obj.longitude = content["geoData"]["longitude"]
        obj.textDescription = textDescription
        obj.imageFileName = name+" Medium.png"
        print ("text description: ", textDescription)
        ## Get image width and height
        image_name = name + " Medium.png"
        # image_file_path = photos_filepath / image_name
        image_file_path = photos_filepath
        im = Image.open(image_file_path)
        width, height = im.size
        obj.imageWidth = width
        obj.imageHeight = height
        
#        obj.printObj()

        if count > 1:
            output_json = output_json + " , "
        output_json  = output_json + obj.toJson() 
        print (obj.toJson())
        
        for key in content.keys():
            if key in output_dir:
                output_dir[key] = output_dir[key] +1
                
            else:
                output_dir[key] = 1
output_json = output_json + " ] }"
# print (output_json)
with open(OUTPUT_FILE, 'w') as outfile:
    outfile.write(output_json)
    
print(output_dir)
