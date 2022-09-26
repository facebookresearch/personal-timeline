import json
from enum import Enum

class EntryType(str, Enum):
    PHOTO: str="photo"
    PURCHASE: str="purchase"
    WORKOUT: str="workout"
    VISIT: str="visit"
    MUSIC: str="music"

    def toJson(self):
        return json.dumps(self.__dict__.values())