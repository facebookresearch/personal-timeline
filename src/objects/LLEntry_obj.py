import json

from typing import List, Dict, Tuple
from geopy import Location

class LLEntry:
    def __init__(self, type: str, startTime, source: str):
        self.type = type
        self.source = source

        #TIME: as experienced by the user (i.e., what timezone they're in)
        self.startTime = startTime 
        self.endTime = startTime #self.startTime -> this should be done during derivation if duration is missing
        self.timezone = None

        #LOCATION start and end. If there's only one, it's the start

        # NEW: use geopy to standardize geolocations
        # NEW: contains the ordered list of start/end locations, or the list of locations in a trip
        self.locations: List[Location] = []
        self.lat_lon: List[Tuple] = []

        # Purchase
        self.purchase_id = None
        self.productName = None
        self.productPrice = None
        self.currency = None
        self.productQuantity = None
        self.author= None

        # Music
        self.artist = None
        self.track = None
        self.playDuration:int = 0
        self.durationUnit = "ms"
        self.track_count={}

        # TEXT of entry (often generated programmatically from source data)
        self.textDescription = None

        # Searchable tags
        self.tags: List[str] = []

        # IMAGE data
        # NEW: store a list of image paths
        self.image_paths: List[str] = []

        #IMAGE data
        self.imageTimestamp:int = 0
        self.imageURL = None
        self.rawImageFilename = None
        self.imageFileName = None
        self.imageFilePath = None
        self.imageCaptions = None
        self.captionEmbedding = None
        self.imageEmbedding = None
        self.imageViews = None
        self.peopleInImage:list = []
        self.imageWidth = None
        self.imageHeight = None

        # Data for quantified entries        
        self.duration = 0
        self.distance = 0
        self.calories = 0
        self.outdoor = 1
        self.temperature = None

        # BOOKKEEPING extra info for convenience
        self.startTimeOfDay = "00:00:00"
        self.endTimeOfDay = "00:00:00"
        self.recordedStartTime = startTime

    def printObj(self):
        print(self.type, self.startTime, self.source, self.peopleInImage)

    def __str__(self):
        return self.type + " " + self.startTime + " " + \
               self.source + " " + self.peopleInImage.__str__()

    def toJson(self):
        return json.dumps(self.__dict__)
        # return json.dumps(self, default=lambda o: o.__dict__,
        #                 sort_keys=True, indent=4)


class LLEntrySummary(LLEntry):
    def __init__(self,
                 type: str,
                 startTime: str,
                 endTime: str,
                 locations: List[str],
                 text_summary: str,
                 photo_summary: List[str],
                 stats: Dict[str, float],
                 objects: Dict[str, List[str]],
                 source: str):
        super().__init__(type, startTime, source)

        # start and end time in isoformat
        self.startTime = startTime
        self.endTime = endTime

        # text summary
        self.textDescription = text_summary

        # lists of path strings of the summary
        self.image_paths = photo_summary
        if len(photo_summary) > 0:
            self.imageFilePath = photo_summary[0]

        # start/end locations, or a list of locations in the trip
        self.locations = locations
        if len(locations) > 0:
            self.startGeoLocation = locations[0]
            self.endGeoLocation = locations[-1]
        else:
            self.startGeoLocation = self.endGeoLocation = None

        # a dictionary of statistics: num_photos, num_activities, etc.
        self.stats = stats

        # a dictionary of objects
        self.objects = objects

        # a list of searchable tags
        self.tags = self.create_tags_from_objects(objects)

    def create_tags_from_objects(self, objects):
        """Make all object names and types searchable
        """
        res = list(objects.keys())
        for val in objects.values():
            res += val
        return res



class LLEntrySummary(LLEntry):
    def __init__(self,
                 type: str,
                 startTime: str,
                 endTime: str,
                 locations: List[str],
                 text_summary: str,
                 photo_summary: List[str],
                 stats: Dict[str, float],
                 objects: Dict[str, List[str]],
                 source: str):
        super().__init__(type, startTime, source)

        # start and end time in isoformat
        self.startTime = startTime
        self.endTime = endTime

        # text summary
        self.textDescription = text_summary

        # lists of path strings of the summary
        self.image_paths = photo_summary
        if len(photo_summary) > 0:
            self.imageFilePath = photo_summary[0]

        # start/end locations, or a list of locations in the trip
        self.locations = locations
        if len(locations) > 0:
            self.startGeoLocation = locations[0]
            self.endGeoLocation = locations[-1]

        # a dictionary of statistics: num_photos, num_activities, etc.
        self.stats = stats

        # a dictionary of objects
        self.objects = objects

        # a list of searchable tags
        self.tags = self.create_tags_from_objects(objects)

    def create_tags_from_objects(self, objects):
        """Make all object names and types searchable
        """
        res = list(objects.keys())
        for object_list in objects.values():
            for item in object_list:
                res.append(item["name"])
        return res