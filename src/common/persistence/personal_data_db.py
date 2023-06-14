# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
# -- Category (Transaction)
#  |-- Data_Source (Bank of America)
#    |-- Personal_Data (
# DB Schema:
# CATEGORY
# -> Has info on higher level category that a data source may belong to.
#    New Category can be created but should be rare)
# ID    Name            Fields
# 1     Travel          <Dict of Field Names to data types>
# 2     Transaction
# 3     Workout
# 4     Music

# DATA_SOURCE :
# ID     Source_Name      Category_Id(FK)    config              Field_Mappings
#  1    Bank of America     2                {json conf}         {Field Mappings to LLEntry}
#  2    Apple Health        3
#  3    Strava              3

# config example
# {"input_directory": "personal-data/bofa",
#  "filetype": "csv"|"json"
# Personal_Data (All data from same source will have to be deleted
# and re-imported as there is no known unique key
#  ID    Source_Id(FK)  timestamp    Data
#   1        1          16342223     (Object based on field mapping)

import sqlite3
import json
import pickle
from pathlib import Path
from sqlite3 import Cursor
import os

from src.common.objects.LLEntry_obj import LLEntry
from src.common.objects.import_configs import DataSourceList

os_path_to_data = os.environ['APP_DATA_DIR'] if 'APP_DATA_DIR' in os.environ else "personal-data/app_data"
class PersonalDataDBConnector:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PersonalDataDBConnector, cls).__new__(cls)
            if not os.path.exists(os_path_to_data):
                print("Path does not exist. Creating", os_path_to_data)
                os.mkdir(os_path_to_data)
            cls.instance.con = sqlite3.connect(os.path.join(os_path_to_data, "raw_data.db"))
            cls.instance.cursor = cls.instance.con.cursor()
            cls.instance.setup_tables()
        return cls.instance

    tables = ["data_source", "personal_data"]

    ddl = {
        "category": "CREATE TABLE category(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "name, fields)",
        "data_source": "CREATE TABLE data_source(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "source_name UNIQUE, entry_type, configs, field_mappings)",
        "personal_data": "CREATE TABLE personal_data(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "source_id, data_timestamp, dedup_key UNIQUE, data, "
                     "imageFileName, imageFilePath UNIQUE,"
                     "location, location_done DEFAULT 0, captions, captions_done DEFAULT 0,"
                     "embeddings, embedding_done DEFAULT 0, status DEFAULT active, dedup_done DEFAULT 0,"
                     "enriched_data, export_done DEFAULT 0,"
                     "FOREIGN KEY(source_id) REFERENCES data_source(id))"
    }

    indexes = {
        "personal_data": [
            'CREATE UNIQUE INDEX "uniq_img_filepath" ON "personal_data" ( "imageFilePath" )',
            'CREATE UNIQUE INDEX "uniq_src_filename" ON "personal_data" ( "source_id", "imageFileName" )'
        ]
    }

    bootstrap_locations = {
        "data_source": "src/common/bootstrap/data_source.json"
    }

    def execute_write(self,sql,params=None):
        if params:
            self.con.commit()
            self.con.execute(sql,params)
        else:
            self.con.commit()
            self.con.execute(sql)
        self.con.commit()

    def get_data_source_location(self):
        return PersonalDataDBConnector.bootstrap_locations["data_source"]

    def setup_tables(self):
        for table in PersonalDataDBConnector.tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='" + table + "'"
            # print("Looking for ", table, "using SQL:: ", lookup_sql)
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = PersonalDataDBConnector.ddl[table]
                print("Creating table: ", table, " using SQL:: ", create_sql)
                self.execute_write(create_sql)
                if table in PersonalDataDBConnector.indexes.keys():
                    for idx_sql in PersonalDataDBConnector.indexes[table]:
                        print("Creating index using SQL:: ", idx_sql)
                        self.execute_write(idx_sql)
            else:
                print("Table ", table, " found.")
            if table in PersonalDataDBConnector.bootstrap_locations.keys():
                print("Bootstrapping...")
                bootstrap_file = PersonalDataDBConnector.bootstrap_locations[table]
                cwd = str(Path().absolute())
                bootstrap_file = cwd + "/" + bootstrap_file
                #print("Reading ", bootstrap_file)
                with open(bootstrap_file, 'r') as f1:
                    r = f1.read()
                    json_data = json.loads(r)
                    #Create Python Class Object from Json
                    ds_list = DataSourceList(json_data)
                    for entry in ds_list.data_sources:
                        self.add_or_replace(table, entry.__dict__, "id")
            else:
                print("No bootstrap data available for ", table)

    def add_or_replace_personal_data(self, key_value: dict, unique_key=None):
        self.add_or_replace("personal_data", key_value, unique_key)
    def add_or_replace(self, table, key_value:dict, unique_key:str=None):
        insert_key_arr = []
        insert_placeholder_arr=[]
        insert_value_arr = []
        update_arr_key = [] # For Upsert using ON CONFLICT command
        update_arr_val = []
        for key in key_value:
            #print("Key:: ", key, " > ", type(key_value.__dict__[key]))
            insert_key_arr.append(key)
            insert_placeholder_arr.append("?")
            if key != unique_key:
                update_arr_key.append(key + "=?")
            if not (isinstance(key_value[key], int) or isinstance(key_value[key], str)):
                update_arr_val.append(pickle.dumps(key_value[key]))
                insert_value_arr.append(pickle.dumps(key_value[key]))
            else:
                if key != unique_key:
                    update_arr_val.append(key_value[key])
                insert_value_arr.append(key_value[key])
        insert_values = tuple(insert_value_arr) + tuple(update_arr_val)

        insert_sql = "INSERT INTO " + table + "(" + ", ".join(insert_key_arr) + ")" \
                     + " values (" + ", ".join(insert_placeholder_arr) + ")"
        if unique_key is not None:
            insert_sql += " ON CONFLICT(" + unique_key + ") DO UPDATE SET " + \
                          ", ".join(update_arr_key)
        # print("Insert SQL:: ", insert_sql,  "data: ", insert_values)
        self.execute_write(insert_sql, insert_values)

    def read_data_source_conf(self, select_cols:str, source_name=None):
        if source_name is not None:
            read_sql = "SELECT " + select_cols + " from data_source where source_name=\""+source_name+"\""
        else:
            read_sql = "SELECT " + select_cols + " from data_source"
        result = self.cursor.execute(read_sql)
        return result.fetchall()

    def search_personal_data(self, select_cols: str, where_conditions: dict=None) -> Cursor:
        where_arr = []
        if where_conditions is not None:
            for key in where_conditions:
                where_arr.append(key + " " + where_conditions[key])
        where_clause = ""
        if len(where_arr) > 0:
            where_clause = " WHERE " + " AND ".join(where_arr)
        lookup_sql = "SELECT " + select_cols + " FROM personal_data " + where_clause
        # print("Searching for personal data using SQL:: ", lookup_sql)
        res = self.cursor.execute(lookup_sql)
        return res

    def add_photo(self, source_id: str, obj: LLEntry):
        pickled_object = pickle.dumps(obj)
        insert_sql = """INSERT INTO personal_data (source_id, data_timestamp, imageFileName, imageFilePath, data)
         values(?,?,?,?,?)"""
        data_tuple = (source_id, int(obj.imageTimestamp), obj.imageFileName, obj.imageFilePath, pickled_object)
        #print("Insert SQL:: ", insert_sql, " data:: ", data_tuple)
        self.execute_write(insert_sql, data_tuple)

    def add_only_photo(self, source_id: str, imageFileName: str, imageFilePath: str):
        insert_sql = """INSERT INTO personal_data (source_id, imageFileName, imageFilePath)
                 values(?,?,?)"""
        data_tuple = (source_id, imageFileName, imageFilePath)
        #print("Insert img only SQL:: ", insert_sql, " data:: ", data_tuple)
        self.execute_write(insert_sql, data_tuple)

    def is_same_photo_present(self, source, filename, timestamp):
        lookup_sql = """SELECT imageFileName FROM personal_data WHERE source_id=? AND imageFileName=? AND data_timestamp=?"""
        data_tuple = (source, filename, timestamp)
        # print("Searching for ", filename, " using SQL:: ", lookup_sql, data_tuple)
        res = self.cursor.execute(lookup_sql, data_tuple)
        if res.fetchone() is None:
            #print(filename, " not found.")
            return False
        else:
            #print(filename, " found.")
            return True

    def print_data_stats_by_source(self):
        stats_sql = """SELECT ds.source_name, COUNT(*) as count
                    from data_source ds LEFT JOIN personal_data pd 
                    on pd.source_id=ds.id 
                    where pd.data is not null
                    group by ds.source_name
                    order by ds.id"""
        res = self.cursor.execute(stats_sql)

        print("Data Stats by source:::")
        print("Source", ": ", "Count")
        for row in res.fetchall():
           print(row[0],": ", row[1])
