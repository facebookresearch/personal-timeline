import pickle
from typing import List

from elasticsearch import Elasticsearch

from datetime import datetime
from elasticsearch_dsl import *
from elasticsearch_dsl.query import MultiMatch, GeoDistance

from src.objects.LLEntry_obj import LLEntry

class LLEntryES(Document):
    #Exact but shrinked version of LLEntry
    type = Keyword() # Comes from EntryType. summary, trip, day, llentry + types specific to llentry: purchase, health
    startTime = Date()
    endTime = Date()
    source = Keyword()
    lat_lon = GeoPoint(multi=True)
    tags = Keyword(multi=True)
    textDescription = Text(analyzer='snowball')
    #Contains original LLEntry Object in pickled state
    obj = Binary()

    class Index:
        name = 'lifelog_summary'
        settings = {
          "number_of_shards": 2,
        }

    def save(self, ** kwargs):
        # self.lines = len(self.body.split())
        return super(LLEntryES, self).save(** kwargs)

    def create_es_document_from(self, inputObj:LLEntry):
        self.meta.id=inputObj.id
        self.type = inputObj.type
        self.startTime = inputObj.startTime
        self.source = inputObj.source
        self.endTime = inputObj.endTime
        self.lat_lon = inputObj.lat_lon
        self.tags = inputObj.tags
        self.textDescription = inputObj.textDescription
        self.obj = pickle.dumps(inputObj)
        return self

class ESHelper:
    def __init__(self):
        # Define a default Elasticsearch client
        connections.create_connection(hosts=['localhost'])
        LLEntryES.init()

    def save(self, entry:LLEntry):
        doc = LLEntryES()
        doc.create_es_document_from(entry)
        doc.save()

    # Wrapper function around Search
    # Input: query_str: Query string containing all words that need to
    #                   be matched across all text/keyword fields
    # Input: geo_distance: Dictionary with following structure
    #     "geo_distance": {
    #         "distance": "2km",
    #         "lat": 32,
    #         "lon": -122
    #     }
    def search(self, query_str:str, geo_distance:dict) -> List[LLEntry]:
        client = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        s = LLEntryES.search()
        if query_str is not None:
            s.query = MultiMatch(
                query=query_str,
                fields=["tags","textDescription"]

            )
        if geo_distance is not None:
            s.filter = GeoDistance(
                distance=geo_distance.get("distance"),
                lat_lon={"lat": geo_distance.get("lat"),
                         "lon": geo_distance.get("lon")}
            )
        response = s.execute()

        output = []
        # print out all the options we got
        for h in response:
            print("%15s: %25s" % (query_str, h.meta.id))
            output.append(pickle.loads(h.obj))
        return output


def test_class():
    # Run the code elasticsearch
    es_helper = ESHelper()

    # create and save and article
    entry = LLEntry("purchase", datetime.now().__str__(),"file")
    entry.id = 1
    entry.lat_lon = [{"lat":32.345, "lon":-122.345},
                     {"lat":-32.345, "lon":122.345}]
    entry.tags = ["hello", "world"]
    entry.textDescription="I am a text Description"
    es_helper.save(entry)

    entry.id = 2
    entry.tags=[]
    es_helper.save(entry)

    article = LLEntryES.get(id=2)
    x = pickle.loads(article.obj)
    print("Object same as original?", entry.equals(x))

    #Prepare for search
    geo_dist = {
        "distance": "10mi",
        "lat": -32.3,
        "lon": 122.3
    }

    output = es_helper.search("hello text",geo_dist)
    for o in output:
        print(o.toJson())

test_class()