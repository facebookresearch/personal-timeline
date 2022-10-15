import json
class LLEntry:
    def __init__(self, type, startTime, source):
        self.type = type
        self.source = source

        #TIME: as experienced by the user (i.e., what timezone they're in)
        self.startTime = startTime 
        self.endTime = self.startTime        
        self.timezone = ""

        #LOCATION start and end. If there's only one, it's the start
        self.startLocation = ""
        self.latitude = "" 
        self.longitude = ""
        self.startCountry = ""
        self.startState = ""
        self.startCity = ""
        self.endLocation = ""
        self.endCountry = ""
        self.endState = ""
        self.endCity = ""
        self.endLatitude = ""
        self.endLongitude = ""

        # Purchase
        self.purchase_id = ""
        self.productName = ""
        self.productPrice = ""
        self.currency = ""
        self.productQuantity = ""
        self.author= ""

        # Music
        self.artist = ""
        self.track = ""
        self.playtimeMs = 0
        self.track_count={}

        # TEXT of entry (often generated programmatically from source data)
        self.textDescription = ""
        
        #IMAGE data
        self.imageURL = ""
        self.imageTimestamp = 0
        self.imageFileName = ""
        self.imageFilePath = ""
        self.imageCaptions = ""
        self.captionEmbedding = ""
        self.imageEmbedding = ""
        self.imageViews = ""
        self.peopleInImage = []
        self.imageWidth = ""
        self.imageHeight = ""

        # Data for quantified entries        
        self.duration = 0
        self.distance = 0
        self.calories = 0
        self.outdoor = 1
        self.temperature = ""

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

class LLEntryInvertedIndex:
    def __init__(self):
        self.index = {}
    def addEntry(self, key:str, entry: LLEntry):
        if key not in self.index.keys():
            self.index[key] = []
        self.index[key].append(entry)

    def getEntries(self, key):
        if key in self.index.keys():
            return self.index[key]
        else:
            return None
    def __str__(self):
        return self.index.__str__()

