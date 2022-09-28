from src.importer.photo_importer_base import PhotoImporter
from src.objects.LLEntry_obj import *
from src.objects.EntryTypes import EntryType

# This is where the photos and their jsons sit
INPUT_DIRECTORY = "personal-data/facebook"
SUB_DIRS = ["posts"]
SOURCE = "Facebook Posts"
TYPE = EntryType.PHOTO

class FacebookPhotosImporter(PhotoImporter):
    def __init__(self):
        super().__init__(INPUT_DIRECTORY, SUB_DIRS, SOURCE, TYPE)

    def import_photos(self, cwd, subdir):
        json_filepath = cwd + "/" + subdir if subdir is not None else cwd
        print("Using path: ", json_filepath)
        json_files = self.get_type_files_deep(json_filepath, ["json"])
        print("All json files in path: ", json_files)
        outputList = LLEntryList()
        sofar=0
        for json_file in json_files:
            print("Reading File: ", json_file)
            with open(json_file, 'r') as f1:
                r = f1.read()
                post_data = json.loads(r)
            #print("post_data is of type: ", type(post_data))
            #Object boundary in FB jsons are at timestamp or creation_timestamp based on post type
            all_media = self.find_all_in_haystack("timestamp", post_data, True)
            ts2 = self.find_all_in_haystack("creation_timestamp", post_data, True)
            all_media += ts2
            #print("Image_Container", all_media)
            for media_container in all_media:
                tagged_people = []
                if isinstance(media_container, dict) and "tags" in media_container.keys():
                    tagged_people = media_container["tags"]
                uri_container = self.find_all_in_haystack("uri", post_data, True)
                count = 0;
                for one_media in uri_container:
                    if isinstance(one_media, dict) and "uri" in one_media.keys():
                        count += 1
                        uri = cwd +"/"+ one_media["uri"]
                        exif_data = self.find_all_in_haystack("exif_data", one_media, False)
                        #print("exif_data: ", exif_data)
                        if exif_data and isinstance(exif_data, list):
                            latitude:float = float(exif_data[0]["latitude"]) if "latitude" in exif_data[0].keys() else 0.0
                            longitude:float = float(exif_data[0]["longitude"]) if "longitude" in exif_data[0].keys() else 0.0
                            taken_timestamp:int = int(exif_data[0]["taken_timestamp"]) \
                                if "taken_timestamp" in exif_data[0].keys() else 0
                            if not self.is_photo_already_processed(self.get_filename_from_path(uri), taken_timestamp):
                                if latitude==0.0 and longitude==0.0 and taken_timestamp==0:
                                    #print("No GPS or Time info, skipping: ", self.get_filename_from_path(uri))
                                    continue
                                obj = self.create_LLEntry(uri, latitude, longitude, taken_timestamp, tagged_people)
                                self.db.add_photo(obj)
                                #print("OBJ: ",obj)
                                outputList.addEntry(obj)
                                sofar += 1
                                if sofar%100==0:
                                    print("Photos imported so far:", len(outputList.getEntries()))
                            # else:
                            #     print(self.get_filename_from_path(uri), " is already processed. Skipping recreation...")
        print("Total Photos Imported:", len(outputList.getEntries()))

# cwd = str(Path(INPUT_DIRECTORY).absolute())
# full_output = LLEntryList()
# for dir in SUB_DIRS:
# output = (cwd, dir)
# print("So Far:::", output.toJson())
# full_output.addEntries(output)
# print(full_output.toJson())