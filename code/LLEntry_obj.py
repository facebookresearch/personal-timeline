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

        # TEXT of entry (often generated programmatically from source data)
        self.textDescription = ""
        
        #IMAGE data
        self.imageFileName = ""
        self.imageCaptions = ""
        self.captionEmbedding = ""
        self.imageEmbedding = ""
        self.imageViews = ""
        self.peopleInImage = ""
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
    def toJson(self):
        return json.dumps(self.__dict__)



