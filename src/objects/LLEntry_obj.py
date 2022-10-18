import json
class LLEntry:
    def __init__(self, type, startTime, source):
        self.type = type
        self.source = source

        #TIME: as experienced by the user (i.e., what timezone they're in)
        self.startTime = startTime 
        self.endTime = None #self.startTime -> this should be done during derivation if duration is missing
        self.timezone = None

        #LOCATION start and end. If there's only one, it's the start
        self.startLocation = None
        self.latitude = None
        self.longitude = None
        self.startCountry = None
        self.startState = None
        self.startCity = None
        self.endLocation = None
        self.endCountry = None
        self.endState = None
        self.endCity = None
        self.endLatitude = None
        self.endLongitude = None

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
        self.duration = None
        self.distance = None
        self.calories = None
        self.outdoor = None
        self.temperature = None

        #BOOKKEEPING extra info for convenience
        self.startTimeOfDay = "00:00:00"
        self.endTimeOfDay =  "00:00:00"
        self.recordedStartTime = startTime

    def printObj(self):
        print(self.type, self.startTime, self.source, self.peopleInImage)

    def __str__(self):
        return self.type +" "+ self.startTime +" "+ self.source +" "+ self.peopleInImage.__str__()

    def toJson(self):
        return json.dumps(self.__dict__)
        #return json.dumps(self, default=lambda o: o.__dict__,
         #                 sort_keys=True, indent=4)

