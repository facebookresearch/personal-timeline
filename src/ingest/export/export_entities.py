import json
from typing import List

from tqdm import tqdm

from src.common.persistence.personal_data_db import PersonalDataDBConnector
import pickle
from geopy.location import Location
from src.common.objects.LLEntry_obj import LLEntry
class PhotoExporter:
    def __init__(self):
        self.db = PersonalDataDBConnector()
        self.export_list: List[LLEntry] = []

    def get_all_data(self):
        if len(self.export_list) == 0:
            self.generate_export_list()
        return self.export_list
    def generate_export_list(self):
        select_cols = "enriched_data"
        where_clause = {"enriched_data": "is not NULL"}
        res = self.db.search_personal_data(select_cols, where_clause)
        count = 0
        for row in tqdm(res.fetchall()):
            count += 1
            data: LLEntry = pickle.loads(row[0])
            self.export_list.append(data.toDict())

    def create_export_entity(self, incremental=True):
        #Read data, location, caption from photos
        select_cols = "id, data, location, captions, embeddings, status"
        where_clause = {"data": "is not NULL"}
        if incremental:
            where_clause["export_done"] = "=0"

        select_count = "count(*)"
        count_res = self.db.search_personal_data(select_count, where_clause)
        pending = count_res.fetchone()
        if pending is None:
            print("No pending exports")
            return
        # print("Total exports to be done: ", pending[0])
        res = self.db.search_personal_data(select_cols, where_clause)
        count = 0
        for row in tqdm(res.fetchall()):
            count += 1
            row_id = int(row[0])
            data: LLEntry = pickle.loads(row[1])
            locations:List[Location] = pickle.loads(row[2]) if row[2] is not None else None
            #print("Processing RowID: ",row_id)
            captions = row[3]
            embeddings = row[4]
            status = row[5]
            if status != 'active':
                print("RowId: ", row_id, "is an identified duplicate, will be unexported")
                self.db.add_or_replace_personal_data({"enriched_data": None, "export_done": 1, "id":row_id}, "id")
                continue
            #Add Location data
            data = self.populate_location(data, locations)
            #Add caption data
            data = self.populate_captions(data, captions)
            #TODO: Add embedding data

            # Add Text Description. Last step after all other attributes are populated
            data = self.populate_text_description(data)

            # Write enriched_data, set enrichment_done to 1
            #print("Writing enriched data:: ", data.toJson())
            self.db.add_or_replace_personal_data({"enriched_data": data, "export_done": 1, "id": row_id}, "id")
        print("Export entities generated for ", count, " entries")
    def populate_location(self, data:LLEntry, locations:Location) -> LLEntry:
        if locations is not None:
            data.locations = locations
            # data.startLocation = str(location)
            # if "country" in location.raw["address"]:
            #     data.startCountry = location.raw["address"]["country"]
            # if "city" in location.raw["address"]:
            #     data.startCity = location.raw["address"]["city"]
            # if "state" in location.raw["address"]:
            #     data.startState = location.raw["address"]["state"]
        return data

    def populate_captions(self, data:LLEntry, captions: list) -> LLEntry:
        if captions is not None:
            #TODO: Add captions
            data.imageCaptions = captions
            return data
        return data

    def populate_text_description(self, data:LLEntry) -> LLEntry:
        if data.textDescription is not None:
            # if textDescription is prepopulated, replace $location placeholder
            if len(data.locations) > 0:
                data.textDescription = data.textDescription.replace("$location", str(data.locations[0]))
        else:
            textDescription = data.startTimeOfDay + ": " + str(data.locations[0])
            textDescription += " with " if len(data.peopleInImage)>0 else ""
            #TODO:Assumes that peopleInImage List has dict with "name" key
            for j in data.peopleInImage:
                textDescription += "\n " + j["name"]

            for j in data.imageCaptions:
                textDescription += ", " + j
            data.textDescription = textDescription
        return data