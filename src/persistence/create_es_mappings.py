from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from datetime import datetime
from elasticsearch_dsl import *

from src.objects.LLEntry_obj import LLEntry

# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])

class LLEntryES(Document):
    type = Keyword()
    startTime = Date()
    endTime = Date()
    startLocation = Text(analyzer='snowball', fields={'raw': Keyword()})
    geoLocation = GeoPoint()
    title = Text(analyzer='snowball', fields={'raw': Keyword()})
    body = Text(analyzer='snowball')
    tags = Keyword()
    published_from = Date()
    lines = Integer()

    class Index:
        name = 'lifelog_summary'
        settings = {
          "number_of_shards": 2,
        }

    def save(self, ** kwargs):
        self.lines = len(self.body.split())
        return super(LLEntryES, self).save(** kwargs)

    def is_published(self):
        return datetime.now() > self.published_from

# create the mappings in elasticsearch
LLEntryES.init()

# create and save and article
# entry = LLEntry("purchase", datetime.now().__str__(),"file")
# entry.latitude = "32.345"
# entry.longitude = "-122.345"
# # article = LLEntryES(meta={'id': 42}, title='Hello world!', tags=['test'])
# article = LLEntryES(entry)
# article.body = ''' looong text '''
# article.published_from = datetime.now()
# article.save()

# article = LLEntryES.get(id=42)
# print("published", article.is_published())

# Display cluster health
print(connections.get_connection().cluster.health())

# client = Elasticsearch([{'host': 'localhost', 'port': 9200}])
#
# s = Search(using=client, index="my-index") \
#     .filter("term", category="search") \
#     .query("match", title="python")   \
#     .exclude("match", description="beta")
#
# s.aggs.bucket('per_tag', 'terms', field='tags') \
#     .metric('max_lines', 'max', field='lines')
#
# response = s.execute()
#
# for hit in response:
#     print(hit.meta.score, hit.title)
#
# for tag in response.aggregations.per_tag.buckets:
#     print(tag.key, tag.max_lines.value)
