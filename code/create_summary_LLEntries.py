import json
import os
from pathlib import Path
import datetime
from datetime import datetime, timedelta
from datetime import timezone
from json_obj import LLEntry
from util import *
import pandas as pd
import numpy as np


# This is where the photos and their jsons sit
HOME_CITIES = ["Los Altos", "Palo Alto", "Mountain View", "San Francisco", "Burlingame", "Milpitas", "San Jose"]
OUTPUT_FILE = "summaries_index.json"
SOLR_OUTPUT_FILE = "../data/summaries.json"
OUTPUT1_FILE = "summaries1_index.json"
GTIMELINE_DIR = "2019"
INPUT_FILE = "../data/date_inverted_index.json"
global summaries
global monthly
global path 
global output_json
global df

def pnice (city, state):
    # print (city, state)
    if state == "" and city == "":
        return ("")
    if state == "":
        return (city)
    if city == "":
        return (state)
    result = city + ", " + state
    return (result)

def nicePrintList(l):
    count = 0
    result = ""
    for item in l:
        if item == "":
            continue
        count = count +1
        if count > 1:
            result = result + ", "
        result = result + item
    return (result)
    
def printTrip(trip):
    # print (trip["locations"])
    
    plocations = {}
    for loc in trip["locations"]:
        
        c = loc[2]
        if c not in plocations:
            plocations[c] = [(loc[0], loc[1])]
        else:
            if (loc[0], loc[1]) not in plocations[c]:
                plocations[c].append((loc[0], loc[1]))
    length = str(trip["end"] - trip["start"])
    result = "Trip starting on " + nDaysAfterEpoch(trip["start"]) + " for " + length + " days, to "
    country_count = 0
    for c in plocations.keys():
        country_count = country_count +1
        if country_count > 1:
            result = result + ", "
        pc = ""
        if c != "United States":
            pc = c
        cs_string = ""
        cs_count = 0
        prev_pnice = ""
        l_pnice = []
        for cs in plocations[c]:
            if cs[0] in HOME_CITIES:
                continue
            l_pnice.append(pnice(cs[0], cs[1])) 
                
            
        nicePrint =  nicePrintList(l_pnice)   
        if c == "United States":
            result = result + nicePrint  
        else:
            result = result + pc
            if nicePrint != "":
                result = result + " (" + nicePrint + ")"
    print (result)
    return (result)        

def homeOrNot(day):
    home = 0
    away = 0
    cities, states, countries = [], [], []
    for loc in day:
        
        if loc[0] != "" and loc[0] not in cities:
            cities.append(loc[0])
        if loc[1] != "" and loc[1] not in states:
            states.append(loc[1]) 
        if loc[2] != "" and loc[2] not in countries:
            countries.append(loc[2])
    
   
    if len(list(set(HOME_CITIES) & set(cities))) > 0: 
        home = 1
    for country in countries:
        if country != "United States":
            away = 1
    for state in states:
        if state != "California":
            away = 1
    if home == 0 and away == 0:
        return ("unknown")
    if home == 1 and away == 0:
        return ("home")
    if home == 0 and away == 1:
        return ("away")
    return ("both")
    # def dict_to_json(dict):
#     new_dict = {}
#     for key in dict:
#         los = []
#         for obj in dict[key]:
#             los.append(obj.toJson)
#         new_dict[key]= los
#     print (new_dict)
#     return(new_dict)

def compute_daily_locations():
    global daily_locations
    daily_locations = {}
    print ("in compute daily locations")
    for index, row in df.iterrows():
        day = int (row["day_num"])
        if day not in daily_locations:
            daily_locations[day] = []
       
        city, state, country = "", "", ""
        if not pd.isna(row["country"]): 
            country = row["country"]    
        if not pd.isna(row["city"]): 
            city = row["city"]
        if not pd.isna(row["state"]): 
            state = row["state"]
        if (city, state, country) not in daily_locations[day] and \
           (city, state, country) != ("", "", ""):
            daily_locations[day].append((city, state, country))
    print (daily_locations)


def calculate_trips():
    days = sorted(list(daily_locations.keys()))
    trips = []
    trip_objs = []
    state = "home"
    for day in days:
        locations = daily_locations[day]
        hon = homeOrNot(locations)
        if state == "home"and (hon =="away" or hon == "both"):
            new_trip = { "start": day, "locations":locations}
            state = "trip"
        elif state =="trip":
            if hon == "away" or hon == "both":
                new_trip["locations"] = new_trip["locations"] + locations
            if hon == "both" or hon == "home":
                new_trip["end"] = day
                trips.append(new_trip)
                state = "home"
                obj_start = dayToDate(new_trip["start"])
                obj_end = dayToDate(new_trip["end"])
                new_trip_obj = LLEntry("monthly", obj_start, "TripInference")
                new_trip_obj.endTime = obj_end
                new_trip_obj.textDescription = printTrip(new_trip)
                trip_objs.append(new_trip_obj)
            
    for trip in trips:
        printTrip(trip)
    return (trip_objs)
    
def create_csv(df):
    count = 0
    with open(path, 'r') as f1:
        r1 = f1.read()
        data = json.loads(r1)
        for day in data.keys():
            objs = data[day]
            summary_obj = LLEntry("daily", day, "V1")
            summaries[day] = [summary_obj]
            for obj in objs:
                #print (obj)
                count = count + 1
                startTime = obj["startTime"]
                date = startTime[0:10]
                day_num = int(daysSinceEpoch(date))

# Putting activity and health objects into a daily summary object                   
                if obj["type"][0:5] == "base:":
                    new_type = "daily:" + obj["type"][5:]
                    source = "V0"
                    startTime = obj["startTime"]
                    distance = obj["distance"]
                    duration = obj["duration"]
                    summary_obj.textDescription = summary_obj.textDescription + "\n" + \
                        obj["textDescription"]
                    
                    row = { "date": date,  "month": date[0:7], "day_num": day_num, "unit": "day", \
                            "activity": obj["type"][5:], \
                            "distance": float(distance), "duration": duration, \
                            "city": obj["startCity"], "country": obj["startCountry"], \
                            "state": obj["startState"], "bookend": "0"  }
                    row_end = { "date": date, "month": date[0:7], "day_num": day_num, "unit": "day", \
                            "activity": obj["type"][5:], \
                            "distance": float(distance), "duration": duration, \
                            "city": obj["endCity"], "country": obj["endCountry"], \
                                "state": obj["endState"], "bookend": "1" }

                    df = df.append(row, ignore_index = True)
                    df = df.append(row_end, ignore_index = True)
                            
                    
#                    

                if obj["type"] == "base/photo":
                    if len(obj["peopleInImage"]) > 0:
                        for j in obj["peopleInImage"]:
#                            people_obj.people.append(j["name"])
                            row = {"date": date, "month": date[0:7], "unit": "day", "person": j["name"], \
                                   "day_num": day_num,  "activity": "photo", \
                                   "city": obj["startCity"], "country": obj["startCountry"], \
                                   "state": obj["startState"], "duration": obj["duration"], \
                                   "location": obj["startLocation"], "bookend": "0" }
                            df = df.append(row, ignore_index = True)
                            #print ("adding ", j["name"])
                    if obj["startLocation"] != "":
                        
                        #if obj["startLocation"] not in location_obj.locations:
                        #    print("adding ", obj["startLocation"])
 #                           location_obj.locations.append(obj["startLocation"])
                        row = {"date": date, "month": date[0:7], "unit": "day", "day_num": day_num, \
                               "location": obj["startLocation"], \
                               "city": obj["startCity"], "country": obj["startCountry"], \
                               "state": obj["startState"], "activity": "photo", "bookend": "0"}
                        df = df.append(row, ignore_index = True)
                #summaries[date].append(location_obj)
                # summaries[date].append(people_obj)

                # if len(location_obj.locations) > 0:
                #     location_obj.textDescription = "Spent the day at"
                #     for place in location_obj.locations:
                #         location_obj.textDescription =  location_obj.textDescription + " " + \
                #             place
                #     location_obj.textDescription = location_obj.textDescription + "."
                # if len(people_obj.people) > 0:
                #     people_obj.textDescription = "Spent the day with"
                #     for person in people_obj.people:
                #         people_obj.textDescription = people_obj.textDescription + " " +  \
                #             person
                #     people_obj.textDescription = people_obj.textDescription + "."
                    
                        
        print(count)
        df.to_csv("summaries.csv")
#        print (df.head())
        return (df)

def return_summary_item(name, l):
    for i in l:
        if i.type == name:
            return (i)
    return False


# def create_monthly_summaries():
#     for day in summaries.keys():
#         month_key = day[0:7]
#         if month_key not in monthly:
#             monthly[month_key] = []
#         for obj in summaries[day]:

#             if obj.type == "daily:running":
# #                print ("found running", obj.distance)
#                 run_obj = return_summary_item("monthly:running", monthly[month_key])
# #               print (run_obj)
#                 if run_obj:
#                     f_d = float(obj.distance)
#                     f_s = float(run_obj.distance)
#                     run_obj.distance = str(f_d + f_s)
# #                    print ("adding :")
#                     #print (month_key, str(f_s))
#                     summary_obj.textDescription = "Ran " + \
#                          truncateStringNum(run_obj.distance,2) + " miles."
#                     # print (summary_obj.textDescription)
#                     # run_obj["run_count"] ++
#                 else:
#                     new_type = "monthly:running"
#                     source = "V0"
#                     startTime = obj.startTime
#                     summary_obj = SolrObj(new_type, startTime, source)
#                     summary_obj.distance = obj.distance
#                     summary_obj.textDescription = \
#                         "Ran " + truncateStringNum(obj.distance,2) + " miles."
#                     monthly[month_key].append(summary_obj)


global df

summaries = {}
jsummaries = {}
# monthly = {}
cwd = Path()
path = cwd / INPUT_FILE

df = pd.DataFrame({"date": [], "month": [], "day_num": [], "unit": [],  "activity": [], "distance": [], "location": [], "person": [], "bookend": []})
print (df)
        
df = create_csv(df)
compute_daily_locations()
trip_summaries = calculate_trips()
for trip in trip_summaries:
    mon = trip.startTime[0:7]
    if mon not in summaries:
        summaries[mon] = [trip]
        jsummaries[mon] = [trip]
    else:
        summaries[mon].append(trip)
        jsummaries[mon].append(trip)
    if not sameMonth(trip.startTime, trip.endTime):
        e_month = trip.endTime[0:7]
        if e_month not in summaries:
            summaries[e_month] = [trip]
            jsummaries[e_month] = [trip]
        else:
            summaries[e_month].append(trip)
            jsummaries[e_month].append(trip)
df1 = df.query('activity == "running" & bookend == "0" ').groupby(by = "month").agg({'distance': ['sum']}).reset_index()


for index, row in df1.iterrows():
        

        mon = row[0]
        tot = truncateStringNum(row[1], 2) 
        if row[1] > 0:
            desc = "Ran " + tot + " miles."
        else:
            desc = "Didn't run this month."
        obj_start = mon + "-01"
                
        new_activity_obj = LLEntry("monthly", obj_start, "Run sum")
        new_activity_obj.textDescription = desc
        if mon not in summaries:
            summaries[mon] = [new_activity_obj]
        else:
            summaries[mon].append(new_activity_obj)
            
            
#create_monthly_summaries()
#summaries.update(monthly)
print(df.head())
count = 0
solr_output = "[ "
c1 = 0
for per in summaries.keys():
    count = count +1
    for element in summaries[per]:
        c1 = c1 +1
        if c1 > 1:
            solr_output = solr_output + " , "
        solr_output = solr_output +  element.toJson()
        
solr_output = solr_output + " ]"
with open(SOLR_OUTPUT_FILE, 'w') as outfile:
    outfile.write(solr_output)

output_path = cwd / OUTPUT_FILE
output_json = json.dumps(dict_to_json(summaries))




with open(OUTPUT_FILE, 'w') as outfile:
    outfile.write(output_json)


output_path = cwd / OUTPUT1_FILE
output_json = "{ "
key_count = 0
for key in summaries.keys():
    key_count = key_count +1
    if key_count > 1:
        output_json = output_json + ", "
    entry_json = '\"' + key + '\"' + ": ["
    item_count = 0
    for item in summaries[key]:
        item_count = item_count +1
        if item_count > 1:
            entry_json = entry_json + ", "
        entry_json = entry_json + item.toJson()
    entry_json = entry_json + "] "
    output_json = output_json + entry_json
    
output_json = output_json + " } "

with open(OUTPUT1_FILE, 'w') as outfile:
    outfile.write(output_json)
