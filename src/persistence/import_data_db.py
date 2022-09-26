import sqlite3
from sqlite3 import Cursor
from src.objects.LLEntry_obj import LLEntry
import pickle


class ImportDataDB:
    tables = ["photos"]

    ddl = {
        "photos": "CREATE TABLE photos(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "source, timestamp, imageFileName, imageFilePath UNIQUE, data, "
                  "location, location_done DEFAULT 0, captions, captions_done DEFAULT 0,"
                  "embeddings, embedding_done DEFAULT 0, status DEFAULT active, dedup_done DEFAULT 0,"
                  "enriched_data, export_done DEFAULT 0)"
    }

    indexes = {
        "photos": [
            'CREATE UNIQUE INDEX "uniq_img_filepath" ON "photos" ( "imageFilePath" )',
            'CREATE UNIQUE INDEX "uniq_src_filename" ON "photos" ( "source", "imageFileName" )'
        ]
    }

    def __init__(self):
        self.con = sqlite3.connect("raw_data.db")
        self.cursor = self.con.cursor()
        self.setup_tables()

    def setup_tables(self):
        for table in ImportDataDB.tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='" + table + "'"
            #print("Looking for ", table, "using SQL:: ", lookup_sql)
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = ImportDataDB.ddl[table]
                print("Creating table: ", table, " using SQL:: ", create_sql)
                self.cursor.execute(create_sql)
                for idx_sql in ImportDataDB.indexes[table]:
                    print("Creating index using SQL:: ", idx_sql)
            #else:
                #print("Table ", table, " found.")

    def add_photo(self, obj: LLEntry):
        pickled_object = pickle.dumps(obj)
        insert_sql = """INSERT INTO photos (source, timestamp, imageFileName, imageFilePath, data)
         values(?,?,?,?,?)"""
        data_tuple = (obj.source, int(obj.imageTimestamp), obj.imageFileName, obj.imageFilePath, pickled_object)
        #print("Insert SQL:: ", insert_sql, " data:: ", data_tuple)
        self.cursor.execute(insert_sql, data_tuple)
        self.con.commit()

    def add_only_photo(self, source: str, imageFileName: str, imageFilePath: str):
        insert_sql = """INSERT INTO photos (source, imageFileName, imageFilePath)
                 values(?,?,?)"""
        data_tuple = (source, imageFileName, imageFilePath)
        #print("Insert img only SQL:: ", insert_sql, " data:: ", data_tuple)
        self.cursor.execute(insert_sql, data_tuple)
        self.con.commit()

    def is_same_photo_present(self, source, filename, timestamp):
        lookup_sql = """SELECT imageFileName FROM photos WHERE source=? AND imageFileName=? AND timestamp=?"""
        data_tuple = (source, filename, timestamp)
        # print("Searching for ", filename, " using SQL:: ", lookup_sql, data_tuple)
        res = self.cursor.execute(lookup_sql, data_tuple)
        if res.fetchone() is None:
            #print(filename, " not found.")
            return False
        else:
            #print(filename, " found.")
            return True

    def search_photos(self, select_cols: str, where_conditions: dict) -> Cursor:
        where_arr = []
        for key in where_conditions:
            where_arr.append(key +" "+ where_conditions[key])
        where_clause = " WHERE " + " AND ".join(where_arr)
        lookup_sql = "SELECT " + select_cols + " FROM photos" + where_clause
        print("Searching for photos using SQL:: ", lookup_sql)
        res = self.cursor.execute(lookup_sql)
        return res

    def update_photos(self, row_id: int, key_value: dict):
        update_arr = []
        data_arr = []
        for key in key_value:
            update_arr.append(key + "=?")
            if key in ["data", "location", "enriched_data"]:
                pickled = pickle.dumps(key_value[key])
                data_arr.append(pickled)
            else:
                data_arr.append(key_value[key])
        data_tuple = tuple(data_arr)
        update_clause = " SET " + ", ".join(update_arr)
        update_sql = "UPDATE photos" + update_clause + " WHERE id=" + str(row_id)
        #print("Updating photos using SQL:: ", update_sql, data_tuple)
        self.cursor.execute(update_sql, data_tuple)
        self.con.commit()
