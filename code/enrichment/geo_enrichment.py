import pytz
import json
import pickle

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from code.objects.LLEntry_obj import LLEntry
from code.persistence.import_data_db import ImportDataDB
from geopy.location import Location

ORIGIN_TIMEZONE = str(pytz.utc)

global geolocator
geolocator = Nominatim(user_agent="pim_photo")

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

class LocationEnricher:
    def calculateLocation(latitude: float, longitude: float) -> Location:
        # location = geolocator.reverse(str(latitude)+","+str(longitude), addressdetails=True)
        location = reverse(str(latitude) + "," + str(longitude), addressdetails=True)
        # location = reverse((50.6539239, -120.3385242), language='en', exactly_one=True)
        print("Location:: ", str(location))
        return location

    def enrich(self):
        db = ImportDataDB()
        select_cols = "id, data"
        where_clause={"location_done": '0'}
        while True:
            res = db.search_photos(select_cols, where_clause)
            count = 0
            for row in res.fetchmany(100):
                count +=1
                row_id = int(row[0])
                data:LLEntry = pickle.loads(row[1])
                print("Data::: ", data.toJson())
                photo_location:Location = LocationEnricher.calculateLocation(data.latitude, data.longitude)
                pickled_location = pickle.dumps(photo_location)
                db.update_photos(row_id, {"location": pickled_location, "location_done": '1'})
            print("Geo Processing completed for ", count, " entries")
            if count==0:
                # Nothing was processed in the last cycle
                break