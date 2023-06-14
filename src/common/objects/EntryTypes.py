# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
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