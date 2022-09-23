import json
from pathlib import Path
from PIL import Image

from code.enrichment.geo_enrichment import LocationEnricher
from code.objects.LLEntry_obj import LLEntry
import pdb

# This is where the photos and their jsons sit
INPUT_DIRECTORY = "../photos/google_photos"
OUTPUT_FILE = "../out/google_photo_data.json"

# Google Photos Configs
SOURCE = "Google Photos"
TYPE = "base/photo"

cwd = Path() # or Path('.')
jsons_filepath = cwd / "../data/photo_filenames.json"
photos_filepath = cwd / INPUT_DIRECTORY
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
        # get lat/long
        latitude = float(content["geoData"]["latitude"])
        longitude = float(content["geoData"]["longitude"])
        taken_timestamp = int(content["photoTakenTime"]["timestamp"])
        real_start_time, utc_start_time = LocationEnricher.calculateExperiencedTimeRealAndUtc(latitude, longitude, taken_timestamp)
        photo_location = LocationEnricher.calculateLocation(latitude, longitude)

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
