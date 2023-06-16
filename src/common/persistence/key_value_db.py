# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import sqlite3
import os

try:
    os_path_to_data = os.environ['APP_DATA_DIR']
except:
    os_path_to_data = "personal-data/app_data"

class CacheDBConnector:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CacheDBConnector, cls).__new__(cls)
            if not os.path.exists(os_path_to_data):
                print("Path does not exist. Creating", os_path_to_data)
                os.mkdir(os_path_to_data)
            cls.instance.con = sqlite3.connect(os.path.join(os_path_to_data, "sqlite_cache.db"), check_same_thread=False)
            cls.instance.cursor = cls.instance.con.cursor()
            cls.instance.setup_tables()
        return cls.instance

    tables = ["geo_cache", "reverse_geo_cache"]

    ddl = {
        "geo_cache": "CREATE TABLE geo_cache(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "key, value)",
        "reverse_geo_cache": "CREATE TABLE reverse_geo_cache(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                     "key, value)"
        }

    indexes = {
        "geo_cache": [
            'CREATE UNIQUE INDEX "uniq_key_gc" ON "geo_cache" ( "key" )'
        ],
        "reverse_geo_cache": [
            'CREATE UNIQUE INDEX "uniq_key_rgc" ON "reverse_geo_cache" ( "key" )'
        ]
    }

    def setup_tables(self):
        for table in CacheDBConnector.tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='" + table + "'"
            # print("Looking for ", table, "using SQL:: ", lookup_sql)
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = CacheDBConnector.ddl[table]
                print("Creating table: ", table, " using SQL:: ", create_sql)
                self.execute_write(create_sql)
                if table in CacheDBConnector.indexes.keys():
                    for idx_sql in CacheDBConnector.indexes[table]:
                        print("Creating index using SQL:: ", idx_sql)
                        self.execute_write(idx_sql)
            # else:
            #     print("Table ", table, " found.")

    def get(self, key:str, table:str) -> str:
        read_sql = "SELECT value from " + table +" where key=\""+key+"\""
        result = self.cursor.execute(read_sql)
        return result.fetchone()

    def put(self,key:str, value:str, table:str):
        insert_sql = "INSERT INTO "+table+" (key, value) values(?, ?)"
        self.execute_write(insert_sql, (key,value))

    def execute_write(self,sql,params=None):
        if params:
            self.con.commit()
            self.con.execute(sql,params)
        else:
            self.con.commit()
            self.con.execute(sql)
        self.con.commit()
