import pickle
from typing import List

from elasticsearch import Elasticsearch

from datetime import datetime
from elasticsearch_dsl import *
from elasticsearch_dsl.query import MultiMatch, GeoDistance, Range, Bool

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
        if entry.endTime == "":
            entry.endTime = entry.startTime
        doc.create_es_document_from(entry)
        doc.save()

    # Wrapper function around Search
    # Input: query_str: Query string containing all words that need to
    #                   be matched across all text/keyword fields
    # Input: search_criteria: Dictionary with following structure:
    # Possible keys: geo_distance(dict), range_query(list)
    #   {
    #       "geo_distance": {
    #         "distance": "2km",
    #         "lat": 32,
    #         "lon": -122
    #       }
    #       "range_query": [
    #           {
    #               "attribute": "startTime",
    #                "range": {
    #                     "lte": 10
    #                }
    #           },
    #           {
    #               "attribute": "endTime",
    #                "range": {
    #                     "gte": "2014-09-05T14:16:56+05:30",
    #                     "lte": "now"
    #                }
    #           }]
    def search(self, query_str:str, search_criteria:dict, geo_distance:dict, range_query:dict) -> List[LLEntry]:
        s = LLEntryES.search()
        if query_str is not None:
            multi_match = MultiMatch(
                query=query_str,
                fields=["tags","textDescription"]
            )
            s = s.query(multi_match)
        # date_range = Range(startTime={"lte":"2014-09-05T14:16:56+05:30"})
        date_range=""
        if range_query is not None:
            if range_query.get("attribute") == "startTime":
                date_range = Range(startTime=range_query.get("range"))
            if range_query.get("attribute") == "endTime":
                date_range = Range(endTime=range_query.get("range"))
            s = s.query(date_range)

        if geo_distance is not None:
            gd_query = GeoDistance(
                distance=geo_distance.get("distance"),
                lat_lon={"lat": geo_distance.get("lat"),
                         "lon": geo_distance.get("lon")}
            )
            s = s.query(gd_query)

        print(s.query.to_dict())
        # print(s.filter.to_dict())
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
    entry = LLEntry("purchase", "2014-09-05T14:16:56+05:30","file")
    entry.id = 1
    entry.lat_lon = [{"lat":32.345, "lon":-122.345},
                     {"lat":-32.345, "lon":122.345}]
    entry.tags = ["hello", "world"]
    entry.textDescription="I am a text Description"
    #es_helper.save(entry)

    entry.id = 2
    entry.tags=[]
    #es_helper.save(entry)

    #Prepare for search
    geo_dist = {
        "distance": "10mi",
        "lat": -32.3,
        "lon": 122.3
    }
    range_query = {
        "attribute": "startTime",
        "range": {"lte":"2014-09-05T14:16:56+05:30"}
    }

    output = es_helper.search("hello text",geo_dist, range_query)
    for o in output:
        print(o.toJson())

test_class()