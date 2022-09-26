import json
import os
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from src.objects.LLEntry_obj import LLEntry
import pytz
from pytz import timezone
from tzwhere import tzwhere
from timezonefinder import TimezoneFinder
from util import *
import time
from geopy.geocoders import Nominatim
import pandas as pd
from os.path import exists

#This is the csv file with the purchases from Amazon (note, digital purchases are separate). 
amazon_purchases_file = "~/Downloads/PIMData/Amazon/Retail.OrderHistory.1.csv"

# This is the csv file with kind purchases should be (when downloaded it's in Digital-Ordering.1/Digital Items.csv
kindle_purchases_file = "~/Downloads/PIMData/Kindle/Digital Items.csv"


OUTPUT_FILE = "amazon_purchases.json"
OUTPUT_DIRECTORY = Path() / "../data"
# This is where the intermediate json files sit

SOURCE = "Amazon"

DEFAULT_TOD_FOR_PURCHASES = " 11:00:00"
exclude_list = ["Kindle Unlimited","Audible Premium Plus", "Prime Membership Fee"]


def purchaseExtract(product, price, date, quantity):
    wtype = "base:purchase"
    print(date)
    print("amazon")
    experienced_startTime = slash_to_dash(str(date)[0:10]) + str(date)[10:19]    
    obj = LLEntry(wtype, experienced_startTime, SOURCE)
    obj.startTimeOfDay = str(date)[11:19]
    textDescription = "Bought " + product + " for price of " + price + " USD "
    if quantity > 1:
        textDescription = textDescription + "(quantity: " + str(quantity) + ")"
    obj.textDescription = textDescription
    return obj



def digitalPurchaseExtract(title, price, currency, date):
    wtype = "base:purchase"
    print(date)
    print("kindle")
    experienced_startTime = str(date) + DEFAULT_TOD_FOR_PURCHASES
    obj = LLEntry(wtype, experienced_startTime, SOURCE)
    obj.startTimeOfDay = DEFAULT_TOD_FOR_PURCHASES
    textDescription = "Bought " + title + " for price of " + str(price) + " " + str(currency)
    obj.textDescription = textDescription
    return obj

def slash_to_dash(date):
    print(date)
    answer = date[6:10] + "-" + date[0:2] + "-" + date[3:5]
    print ("answer is ", answer)
    return answer

def MDYY_to_dash(date):
    print ("input date is ", date)
    if len(date) == 10:
        return date
    print(date)
    mdy = date.split("/")
    y = mdy[2]
    if len(y) == 2:
        y = "20" + y
    m = mdy[1]
    if len(m) < 2:
        m = "0" + m
    d = mdy[0]
    if len(d) < 2:
        d = "0" + d
    answer = y + "-" + m + "-" + d
    #print(mdy)
    return answer
    
output_json = '{ "solrobjects": [ '  
output_path = OUTPUT_DIRECTORY / OUTPUT_FILE

if os.path.exists(Path(amazon_purchases_file)):
    print("found file")
else:
    print("didn't file the file")

    
print("input amazon path is " + amazon_purchases_file)
print("input kindle path is " + kindle_purchases_file)
print("output path is " + str(output_path))

count = 0
try:
    df = pd.read_csv(amazon_purchases_file)
except IOError:
    print('Could not find Amazon purchases CSV file.')
else:
    
    for index, row in df.iterrows():
        if row["Product Name"] not in exclude_list:
            count = count + 1
            if count < 10: 
                print (row["Product Name"], str(row["Unit Price"]), str(row["Order Date"]), str(row["Quantity"]))
            if count > 1:
                output_json = output_json + " , "
                
            output_json = output_json + purchaseExtract(row["Product Name"], str(row["Unit Price"]), str(row["Order Date"]), row["Quantity"]).toJson()
   
    print ("Number of Amazon records is: ")
    print (count )

intermediate_count = count    
try:
    df = pd.read_csv(kindle_purchases_file)
except IOError:
    print('Could not find Kindle purchases CSV file.')
else:

    for index, row in df.iterrows():
        if row["Title"] not in exclude_list:
            count = count + 1
            if count < intermediate_count + 10: 
                print (row["Title"], row["OurPrice"], row["OurPriceCurrencyCode"],  MDYY_to_dash(str(row["OrderDate"])))
            if count > 1:
                output_json = output_json + " , "
            output_json = output_json + digitalPurchaseExtract(row["Title"], row["OurPrice"], row["OurPriceCurrencyCode"], MDYY_to_dash(str(row["OrderDate"]))).toJson()
   
    print ("Number of Kindle records is: ")
    print (count - intermediate_count )
    output_json = output_json + " ] } "
    with open(output_path, 'w') as outfile:
        outfile.write(output_json)

            

    

     
