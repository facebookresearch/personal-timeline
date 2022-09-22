import sqlite3

from code.objects.LLEntry_obj import LLEntry

class ImportDataDB:
    tables = ["photos"]

    ddl = {
        "photos": "CREATE TABLE photos(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "source, timestamp, imageFileName, imageFilePath, data, "
                  "location, location_done DEFAULT 0, captions, captions_done DEFAULT 0,"
                  "embeddings, embedding_done DEFAULT 0, status DEFAULT active, dedup_done DEFAULT 0)"
    }

    # indexes = {
    #     "photos": [
    #         "CREATE INDEX source_timestamp ON tags (title, description);"
    #     ]
    # }

    def __init__(self):
        self.con = sqlite3.connect("raw_data.db")
        self.cursor = self.con.cursor()
        self.setup_tables()

    def setup_tables(self):
        for table in ImportDataDB.tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='"+table+"'"
            print("Looking for ", table, "using SQL:: ", lookup_sql)
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = ImportDataDB.ddl[table]
                print("Creating table: ", table, " using SQL:: ", create_sql)
                self.cursor.execute(create_sql)
            else:
                print("Table ", table, " already exists.")

    def add_photo(self, obj:LLEntry, is_enriched:bool=True):
        insert_sql = """INSERT INTO photos (source, timestamp, imageFileName, imageFilePath, data)
         values(?,?,?,?,?)"""
        data_tuple = (obj.source, int(obj.imageTimestamp), obj.imageFileName, obj.imageFilePath, obj.toJson())
        print("Inserting SQL:: ", insert_sql, " data:: ", data_tuple)
        self.cursor.execute(insert_sql, data_tuple)
        self.con.commit()

    def is_same_photo_present(self, source, filename, timestamp):
        lookup_sql = """SELECT imageFileName FROM photos WHERE source=? AND imageFileName=? AND timestamp=?"""
        data_tuple = (source, filename, timestamp)
        print("Searching for ", filename, "using SQL:: ", lookup_sql, data_tuple)
        res = self.cursor.execute(lookup_sql, data_tuple)
        if res.fetchone() is None:
            print(filename, " not found.")
            return False
        else:
            print(filename, " found.")
            return True