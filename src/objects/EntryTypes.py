import json
from enum import Enum

class EntryType(str, Enum):
    PHOTO: str="photo"
    PURCHASE: str="purchase"
    HEALTH: str="health"
    VISIT: str="visit"
    STREAMING: str="streaming"

    def toJson(self):
        return json.dumps(self.__dict__.values())