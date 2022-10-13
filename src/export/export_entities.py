from tqdm import tqdm

from src.persistence.photo_data_db import PhotoDataDB
import json
import pickle
from geopy.location import Location
from src.objects.LLEntry_obj import LLEntry
class PhotoExporter:

    def __init__(self):
        self.db = PhotoDataDB()
    def create_export_entity(self):
        #Read data, location, caption from photos
        select_cols = "id, data, location, captions, embeddings, status"
        where_clause = {"export_done": "=0", "data":"is not NULL"}
        select_count = "count(*)"
        count_res = self.db.search_photos(select_count, where_clause)
        pending = count_res.fetchone()
        if pending is None:
            print("No pending exports")
            return
        # print("Total exports to be done: ", pending[0])
        res = self.db.search_photos(select_cols, where_clause)
        count = 0
        for row in tqdm(res.fetchall()):
            count += 1
            row_id = int(row[0])
            data: LLEntry = pickle.loads(row[1])
            location:Location = pickle.loads(row[2]) if row[2] is not None else None
            #print("Processing RowID: ",row_id)
            captions = row[3]
            embeddings = row[4]
            status = row[5]
            if status != 'active':
                print("RowId: ", row_id, "is an identified duplicate, will be unexported")
                self.db.update_photos(row_id, {"enriched_data": None, "export_done": 1})
                continue
            #Add Location data
            data = self.populate_location(data, location)
            #Add caption data
            data = self.populate_captions(data, captions)
            #TODO: Add embedding data

            # Add Text Description. Last step after all other attributes are populated
            data = self.populate_text_description(data)

            # Write enriched_data, set enrichment_done to 1
            #print("Writing enriched data:: ", data.toJson())
            self.db.update_photos(row_id, {"enriched_data": data, "export_done": 1})
        print("Export entities generated for ", count, " entries")
    def populate_location(self, data:LLEntry, location:Location) -> LLEntry:
        if location is not None:
            data.startLocation = str(location)
            if "country" in location.raw["address"]:
                data.startCountry = location.raw["address"]["country"]
            if "city" in location.raw["address"]:
                data.startCity = location.raw["address"]["city"]
            if "state" in location.raw["address"]:
                data.startState = location.raw["address"]["state"]
        return data

    def populate_captions(self, data:LLEntry, captions: list) -> LLEntry:
        if captions is not None:
            #TODO: Add captions
            data.imageCaptions = captions
            return data
        return data

    def populate_text_description(self, data:LLEntry) -> LLEntry:
        textDescription = data.startTimeOfDay + ": " + data.startLocation
        textDescription += " with " if len(data.peopleInImage)>0 else ""
        #TODO:Assumes that peopleInImage List has dict with "name" key
        for j in data.peopleInImage:
            textDescription += "\n " + j["name"]

        for j in data.imageCaptions:
            textDescription += ", " + j
        data.textDescription = textDescription
        return data