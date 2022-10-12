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

from src.objects.LLEntry_obj import LLEntry
from src.objects.import_configs import DataSourceList, DataSource


class PersonalDataDBConnector:
    tables = ["data_source", "personal_data"]

    ddl = {
        "category": "CREATE TABLE category(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "name, fields)",
        "data_source": "CREATE TABLE data_source(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "source_name UNIQUE, entry_type, configs, field_mappings)",
        "personal_data": "CREATE TABLE personal_data(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "source_id, data_timestamp, dedup_key UNIQUE, data, FOREIGN KEY(source_id) REFERENCES data_source(id))"
    }

    bootstrap_locations = {
        "data_source": "src/bootstrap/data_source.json"
    }

    def __init__(self):
        self.con = sqlite3.connect("raw_data.db")
        self.cursor = self.con.cursor()

    def setup_tables(self):
        for table in PersonalDataDBConnector.tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='" + table + "'"
            # print("Looking for ", table, "using SQL:: ", lookup_sql)
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = PersonalDataDBConnector.ddl[table]
                print("Creating table: ", table, " using SQL:: ", create_sql)
                self.cursor.execute(create_sql)
            else:
                print("Table ", table, " found.")
            if table in  PersonalDataDBConnector.bootstrap_locations.keys():
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
        #print("Insert SQL:: ", insert_sql,  "data: ", insert_values)
        self.cursor.execute(insert_sql, insert_values)
        self.con.commit()

    def read_data_source_conf(self, select_cols:str, source_name=None):
        if source_name is not None:
            read_sql = "SELECT " + select_cols + " from data_source where source_name=\""+source_name+"\""
        else:
            read_sql = "SELECT " + select_cols + " from data_source"
        result = self.cursor.execute(read_sql)
        return result.fetchall()

# p = PersonalDataDBConnector()
# p.setup_tables()
# print(p.read_data_source_conf("configs","AppleHealth")[0][0])
# print(pickle.loads(p.read_data_source_conf("configs","AppleHealth")[0][0]).__dict__)
# print(pickle.loads(p.read_data_source_conf("field_mappings","AppleHealth")[0][0])[4].__dict__)