import PySimpleGUI as sg
import os
import os.path
import json
from pathlib import Path
import datetime
from datetime import datetime
from datetime import timezone
from src.objects.LLEntry_obj import LLEntry
from operator import itemgetter
from util import *

ROOT_DIR = "/Users/ayh/Documents/src/pim/src/pim-photos/data/"
INDEX_FILE = "date_inverted_index.json"
SUMMARY_FILE = "summaries1_index.json"
summary_path = ROOT_DIR + SUMMARY_FILE
index_path = ROOT_DIR +  INDEX_FILE
image_directory_path = "/Users/ayh/Documents/src/pim/src/pim-photos/photos/"

DUMMY_PHOTO =  image_directory_path + "dayinlife.png"
DEFAULT_YEAR = "2019"
IMAGE_HEIGHT = 600.0
DEFAULT_IMAGE_WIDTH = 500.0
INITIAL_DATE = "2019-01-01"
    
def update_activity_summary(hour):
    text = ""
    for j in range(len(activity_texts)):
        if activity_tod_start[j] > int(hour) or activity_tod_end[j] < int(hour):
            continue
        else:
            text = text + activity_texts[j] + "\n"
    for j in range(len(health_texts)):
        if health_tod_start[j] > int(hour) or health_tod_end[j] < int(hour):
            continue
        else:
            text = text + health_texts[j] + "\n"
    
    window.Element('-NOWSUM-').update(text)

def create_empty_hour_index():
    result = []
    for i in range(0,24):
        result.append(-1) 
    return (result)

def create_hour_index(event_list):
    print ("creating hour index with ")
#    print (event_list)
    result = []
    for i in range(0,24):
        result.append(-1) 
    if len(event_list) == 0:
        return result
    current_event = -1
    for j in range(0, len(event_list)):
        if j == 0:
            result[event_list[j]] = j
        else: 
            if event_list[j] > event_list[j-1]:
                result[event_list[j]] = j
    print(result)
    for i in range(0,len(result)-1):
        if result[i+1] == -1:
            result[i+1] = result[i] 
               
    return result

def clear_previous_day():
#    window.Element("-TIMELINE-").Update(" ")
#    window.Element('-HEALTH-').update(" ")
    window.Element("-PHOTODATA-").update(" ")
    window.Element("-NOWSUM-").update(" ")
    image_count = 0
    image_files = []
    image_texts = []
    image_widths = []
    health_text = ""
    activity_text = ""
    activity_tod_start = []
    health_tod_start = []
    image_tod_start = []
    activity_tod_end = []
    health_tod_end = []
    health_texts = []
    images_index = create_empty_hour_index()
    activity_texts = []
    print ("exiting clear_previous_day")

def clear_previous_month():
    window.Element("-MONTHSUM-").update(" ")

def empty_day(why_text):
    clear_previous_day()
    window.Element("-TOUT-").update(why_text)
    window.Element("-IMAGE-").update(size=(DEFAULT_IMAGE_WIDTH, IMAGE_HEIGHT),filename=DUMMY_PHOTO)



    
def update_image():
    print (current_image)
    print (image_count)
    if current_image == -1:
        image_filepath =   DUMMY_PHOTO
    else:
        current_medium_image = image_files[current_image].replace("Large","Medium")
        image_filepath =  image_directory_path + current_medium_image
        print (image_filepath)
        window.Element("-PHOTODATA-").update(image_texts[current_image])
        window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count))
        if image_count > 1 and current_image < 1:
            window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count) + " (first photo of the day)")
        elif current_image == image_count -1:
            window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count) + " (last photo of the day)")
        
                
        window.Element("-IMAGE-").update(size=(image_widths[current_image], IMAGE_HEIGHT),filename=image_filepath)
    

def getImageRatio (path):
    im = Image.open(path)
    width, height = im.size
    return (width/height)


def showADay(date):
    global image_count 
    global image_files 
    global image_texts 
    global health_text 
    global activity_text
    global current_image
    global todImages
    global todEvents
    global health_tod_start
    global health_tod_end
    global activity_tod_start
    global image_tod_start
    global activity_tod_end
    global images_index
    global events_index
    global image_widths
    global health_texts 
    global activity_texts 
    global str_month
    global str_dom
    global str_year
    
    print ("Showing ", date)

# Generating month description 
    month_display_string = ""
    if date[0:7] in summaries:
        summary_items = summaries[date[0:7]]
        print(summary_items)
        print("length is ")
        print(len(summary_items))
        for i in summary_items:
            print("i is ")
            print(i)
            print ("text description is ")
            print (i["textDescription"])
            month_display_string = month_display_string + i["textDescription"] + "\n"

    window.Element("-MONTHSUM-").update(month_display_string)

# If there's nothing about the date in the index, clear the panels.

    if date not in index:
        reason = "No data for " + date
        empty_day(reason)
        print ("Didn't find date")
        return
    
    window.Element("-TOUT-").Update("Showing " + date)
    unordered_obj = index[date]
    ordered_obj = sorted(unordered_obj, key=itemgetter('startTime'))

    image_count = 0
    image_files = []
    image_texts = []
    image_widths = []
    health_text = ""
    activity_text = ""
    activity_tod_start = []
    health_tod_start = []
    image_tod_start = []
    activity_tod_end = []
    health_tod_end = []
    health_texts = []
    activity_texts = []
    day_display_string = ""

# Generate the daily summary (consists of all the health and timeline data)

    if date in summaries:
        summary_items = summaries[date]
        for i in summary_items:
            print(i["textDescription"])
            day_display_string = day_display_string + i["textDescription"] + "\n"

    window.Element("-DAYSUM-").update(day_display_string)
    

# Iterating over the entries for the day (either photos or other activities)
    print ("STARTING OBJ LOOP!!!!!!!!!!!!!")
    for obj in ordered_obj:
        if obj["type"] == "base/photo": # creating the list of photos
            image_count = image_count +1
            image_files.append(obj["imageFileName"])
            image_texts.append(obj["textDescription"].replace("\n", ","))
            image_width = float(obj["imageWidth"])
            image_height = float(obj["imageHeight"])
            adjusted_height = image_width/image_height * IMAGE_HEIGHT
            image_widths.append(adjusted_height)
            image_tod_start.append(int(obj["startTimeOfDay"][0:2]))

        elif obj["source"] == "AppleHealth":
            health_text = health_text + obj["textDescription"] + "\n"
            print("one more health entry " + obj["startTimeOfDay"][0:2])
            print(obj["textDescription"])
            activity_tod_start.append(int(obj["startTimeOfDay"][0:2]))
            activity_tod_end.append(int(obj["endTimeOfDay"][0:2]))
            activity_texts.append(obj["textDescription"])
        elif obj["source"] == "Google Timeline":
            activity_text = activity_text + obj["textDescription"]  + "\n"
            print ("one more activity entry "+ obj["startTimeOfDay"][0:2])
            print(obj["textDescription"])
            print (obj)
            activity_tod_start.append(int(obj["startTimeOfDay"][0:2]))
            activity_tod_end.append(int(obj["endTimeOfDay"][0:2]))
            activity_texts.append(obj["textDescription"])

    # print ("start time of images")
    # for j in image_tod_start:
    #     print (j)
    # print ("start time of activities")
    # for j in range(len(activity_tod_start)):
    #     print (activity_tod_start[j], activity_texts[j])
    
   
    images_index = create_hour_index(image_tod_start)
    events_index = create_hour_index(activity_tod_start)
    print ('image index')
    print (images_index)
        
    print ("number of images found: ")
    print (image_count)
    if image_count < 2:
        window['-NEXT-'].update(disabled=True)
        window['-PREV-'].update(disabled=True)
    else:
        window['-NEXT-'].update(disabled=False)
        window['-PREV-'].update(disabled=False)
    if image_count == 0:
        window.Element("-PHOTOINDEX-").update("No photos found for the day. ")
        image_filepath =   DUMMY_PHOTO
        window.Element("-IMAGE-").update(size=(DEFAULT_IMAGE_WIDTH, IMAGE_HEIGHT),filename=image_filepath)
                
    # if activity_text == "":
    #     activity_text = "No timeline data to show for the day"
    # if health_text == "":
    #     health_text = "No Apple Health data to show for the day"
        
   
#    window.Element("-TIMELINE-").Update(activity_text)
#    window.Element('-HEALTH-').update(health_text)
    if image_count > 0:
        current_image = 0
        current_medium_image = image_files[current_image].replace("Large","Medium")
                    #image_filepath =  image_directory_path + image_files[current_image]
        image_filepath =  image_directory_path + current_medium_image
        print (image_filepath)
        window.Element("-PHOTODATA-").update(image_texts[current_image])
        window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count))
                    
        window.Element("-IMAGE-").update(size=(image_widths[current_image], IMAGE_HEIGHT),filename=image_filepath)
                    #window['-IMAGE-'].update(data=image_filepath)

                    
# cwd = Path()
#index_path = cwd / INDEX_FILE

str_month = "01"
str_dom = "01"
str_year = "2019"
images_index = create_empty_hour_index()
activity_texts = []
health_texts = []


    
with open(index_path, 'r') as f1:
    print (index_path)
    r1 = f1.read()
    index = json.loads(r1)


with open(summary_path, 'r') as f2:
    r2 = f2.read()
    data = json.loads(r2)
    
global summaries
summaries = {}

# for k in data:
#     count = 0
#     for k in data.keys():
#         summaries[k] = json.loads(data[k]) #returns a list of dicts (= objs)


for k in data.keys():
    summaries[k] = data[k]

# First the window layout in 2 columns

top_section = [
    [
        sg.Text("Select a day (YYYY-MM-DD)"),
        sg.In(size=(25, 1), enable_events=True, key="-DAY-"),
        sg.Button("Show Day", key="-SHOW-"),
        
    ],
]


photos_frame = [
    [sg.Button("Previous photo", key="-PREV-"),
        sg.Button("Next photo", key="-NEXT-"),
     sg.Text(size=(40,1), font='Arial 16', key="-PHOTOINDEX-")],
    
    [sg.Image(key="-IMAGE-")],
    [sg.Text(size=(65, 3), font='Arial 16', key="-PHOTODATA-")],
    ]

# timeline_frame = [
        
#         [sg.Text("Timeline of the day", font='Arial 18')],
#         [sg.Multiline(size=(30, 10), autoscroll = True,font='Arial 14', key="-TIMELINE-")],
        
    
# ]

# activity_frame = [
        
#         [sg.Text("Physical activity of the day",font='Arial 18')],
#         [sg.Multiline(size=(30, 10), autoscroll = True,font='Arial 14', key="-HEALTH-")],
# ]

month_select = [
    [ sg.Slider(range=(1,12), size=(100,20), tick_interval = 1, disable_number_display=False,  expand_x=True, enable_events=True, orientation='horizontal', key="-MONTH-")],
]
year_select = [
    [ sg.Slider(range=(2018,2022), size=(100,20), tick_interval = 1, disable_number_display=False,  expand_x=True, enable_events=True, orientation='horizontal', key="-YEAR-")],
]

month_summary = [
    [ sg.Multiline("Month summary: ",  size=(60,5),  font=("Helvetica", 16), background_color='ivory',  key="-MONTHSUM-")],
]


day_select = [
        [   sg.Slider(range=(1,31), size=(100,20),  tick_interval = 1, expand_x=True, enable_events=True, orientation='horizontal', key='-DOM-')],
    ]

day_summary = [
    [ sg.Multiline("Day summary: ",  size=(60,5),  font=("Helvetica", 16), background_color='ivory',  key="-DAYSUM-")],
]

now_activity_summary = [
    [ sg.Multiline("Activities during this hour: ",  size=(60,5),  font=("Helvetica", 16), background_color='ivory',  key="-NOWSUM-")],
]


hour_select = [
        [ sg.Slider(range=(0,23), size=(100,20),  tick_interval = 1, expand_x=True, enable_events=True,  font=("Helvetica", 15), orientation='horizontal', key='-HOUR-')],
       ]
    

# ----- Full layout -----
layout = [
    [
        sg.Column(top_section, vertical_scroll_only=True)
    ],
    [
        sg.Text(" ", size=(25, 1),font='Courier 18', key="-TOUT-")
    ],
    [ sg.Frame("Select a year", year_select),   
    ],
    [ sg.Frame("Select a month", month_select),  sg.Frame("Month summary", month_summary),  
    ],
#    [ sg.Frame("Month summary", month_summary),  
#    ],
    
    [ sg.Frame("Select a day in the month", day_select),  sg.Frame("Day summary", day_summary),  
    ],
#    [ sg.Frame("Day summary", day_summary),  
#    ],

    [ sg.Frame("Select an hour of the day", hour_select),  sg.Frame("Activities now", now_activity_summary),
    ],
    [
    
       [ sg.Frame("Photos of the day", photos_frame),]
        # sg.Frame("From Google Timeline",  timeline_frame),
        # sg.Frame("From Apple Health", activity_frame)]
        ],

    ]
    
#    [
#        sg.Frame("From Google Timeline",  timeline_frame),
#        sg.Frame("From Apple Health", activity_frame)
#    ]


window = sg.Window("Browse Your Life",  layout)
int_month = 10
int_dom = 10
int_year = 2019
image_count = -1
# event, values = window.read()

# showADay(INITIAL_DATE)
#started = False

# Run the Event Loop
while True:
    event, values = window.read()
            
    if event == "-HOUR-":
        hour = int(values["-HOUR-"])
        current_image = images_index[hour]
        window.Element("-TOUT-").Update("Showing " + str_year + "-" + str(int_month) +
                                        "-" + str(int_dom) + "  " +
                                        str(int(values["-HOUR-"])) + ":00")
        update_image()
        update_activity_summary(hour)
        
    if event == "-YEAR-":
        clear_previous_day()
        clear_previous_month()
        print("found year")
        int_year = int(values["-YEAR-"])
        str_year = str(int_year)
        int_dom = 1
        str_dom = "01"
        str_month = "01"
        constructed_date = str_year + "-" + str_month + "-01"
        print ("constructing: ", constructed_date)
        showADay(constructed_date)

    if event == "-MONTH-":
        clear_previous_day()
        clear_previous_month()
        print("found month")
        int_month = int(values["-MONTH-"])
        int_dom = 1
        str_dom = "01"
        if int_month < 10:
            str_month = "0" + str(int_month)
        else:
            str_month = str(int_month)
        constructed_date = str_year + "-" + str_month + "-01"
        print ("constructing: ", constructed_date)
        showADay(constructed_date)

    if event == "-DOM-":
        clear_previous_day()
        print("found day of month")
        int_dom = int(values["-DOM-"])
        if int_dom < 10:
            str_dom = "0" + str(int_dom)
        else:
            str_dom = str(int_dom)
        constructed_date = str_year + "-" + str_month + "-" + str_dom
        print ("constructing: ", constructed_date)
        showADay(constructed_date)
        
    if event == "-DAY-":
        print ("day event")
        

    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    if event == "-NEXT-":
        print("next")
        current_image = (current_image +1) % len(image_files)
        current_medium_image = image_files[current_image].replace("Large","Medium")
        image_filepath =  image_directory_path + current_medium_image
        print (image_filepath)
        update_image()
        #window.Element("-PHOTODATA-").update(image_texts[current_image])
        #window.Element("-IMAGE-").update(size=(image_widths[current_image], IMAGE_HEIGHT),filename=image_filepath)
        #window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count))

    if event == "-PREV-":
        print("previous")
        current_image = (current_image -1) % len(image_files)
        current_medium_image = image_files[current_image].replace("Large","Medium")
        image_filepath =  image_directory_path + current_medium_image
        print (image_filepath)
        update_image()
        #window.Element("-PHOTODATA-").update(image_texts[current_image])
        #window.Element("-IMAGE-").update(size=(image_widths[current_image], IMAGE_HEIGHT),filename=image_filepath)
        #window.Element("-PHOTOINDEX-").update(xOfy(current_image, image_count))

                                         
    if event == "-SHOW-":
        print ("found show event")
        date = values["-DAY-"]
        
        print(date)
        if len(date) != 10:
            print ("Can't recognize date")
            empty_day("Can't recognize date")
        else:
            str_month = extract_month(date)
            str_dom = extract_DOM(date)
            int_month = int(str_month)
            int_dom = int(str_dom)
            showADay(date)
                
#                window.Element("-TOUT-").Update("No data for " + date)
#                window.Element("-TIMELINE-").Update("Sleepy day")
#                image_filepath =  image_directory_path / DUMMY_PHOTO
#                window.Element("-IMAGE-").update(size=(DEFAULT_IMAGE_WIDTH, IMAGE_HEIGHT),filename=image_filepath)
#                window.Element('-HEALTH-').update("Sleepy day")
                
        

window.close()