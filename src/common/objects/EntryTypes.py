import json
from enum import Enum

class EntryType(str, Enum):
    PHOTO: str="photo"
    PURCHASE: str="purchase"
    HEALTH: str="health"
    VISIT: str="visit"
    STREAMING: str="streaming"
    DAY: str="day"
    TRIP: str="trip"
    ACTIVITY: str="activity"

    def toJson(self):
        return json.dumps(self.__dict__.values())