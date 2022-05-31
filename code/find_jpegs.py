import os
import json

def json_file (file_name):
    return file_name.endswith(".json")

def jpeg_file (file_name):
    return file_name.endswith(".jpeg")

def heic_file (file_name):
    return file_name.endswith(".HEIC")

json_files = []
name_files = []
output_json = "[ "
output_dir = {}

# This is the directory where the photos and jsons are expected to be. Make sure it matches what you have. 
photos_dir = os.listdir("../photos")
OUTPUT_FILE_NAME = '../data/photo_filenames.json'

count = 0
jpeg_count = 0
heic_count = 0

for f in photos_dir:
    if json_file(f):
        count = count +1
    if jpeg_file(f):
        jpeg_count = jpeg_count +1 
    if heic_file(f):
        heic_count = heic_count +1 

print("number of json files is " + str(count))
print("number of jpeg files is " + str(jpeg_count))
print("number of heic files is " + str(heic_count))

for f in photos_dir:
    if json_file(f):
        name = f[:-5][0:-4]
        if name.endswith(".HEIC"):
            name = name[:-5]
    
        jpg = name + ".jpeg"
        if jpg in photos_dir:
            output_dir[name] = jpg
            name_files.append(name)
            json_files.append(f)

print (len(json_files))
print (len(name_files))


out_string = json.dumps(output_dir)

with open(OUTPUT_FILE_NAME, 'w') as outfile:
    outfile.write(out_string)

