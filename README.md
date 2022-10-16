This file explains how to create LifeLog entries from several data sources.


In the explanation, we'll assume three directories all sitting within the application directory:
  code, data, photos
  All code should be run in the code directory. Photos should be stored in the photos directory. The data directory will contain the json files that are created in the process of building the lifelog.

# Step 0: Create environment
1. Install Conda from 
https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
2. Add conda-forge channel:  
   ```conda config --append channels conda-forge```

3. Create a new conda dev environment  
    ```conda create --name <env> python==3.7.13```

4. Install required packages from requirements.txt file:  
    ```conda install --name <env> --file requirements.txt```
5. Activate the newly created environment  
    ```conda activate <env>```
6. Create a new directory under your home folder (this is where all your personal-data will be downloaded)  
    ```$ mkdir ~/personal-data```
7. In your repo, create a Sym link for the above created dir  
    ```$ ln -s ~/personal-data personal-data```

# Step 1: Downloading your photos

### GOOGLE PHOTOS
1. You need to download your Google photos from [Google Takeout](https://takeout.google.com/).  
The download from Google Takeout would be in multiple zip files. Unzip all the files.

2. It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg  
The easiest way to do this on a Mac is:

     -- Select the .HEIC files you want to convert.   
     -- Right click and choose "quick actions" and then you'll have an option to convert the image.  
     -- If you're converting many photos, this may take a few minutes.
3. Create a new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/google_photos```
4. Move all the unzipped folders inside `personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.

### FACEBOOK DATA
1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=your_facebook_information) 
2. Click on <b>Download your information</b> and download FB data in JSON format
3. Create a new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/facebook```
3. Unzip the downloaded file and copy the directory `posts` sub-folder to the above folder. The `posts` folder would sit directly under the facebook folder.


# Step 2: Import your photo data to SQLite (this is what will go into the episodic database)

Run:
    ```
    python -m src.workflow
    ```
The script will allow you to choose the steps you want to run from the workflow.  
Follow the instructions to import and enrich data.

# Step 3: Create Inverted Index Files:

1. Create a data directory and a sym link to that directory inside the repo  
    ```$ mkdir ~/data```  
    ```$ ln -s ~/data```
2. Run  
    ```$ python -m src.create_index```
    This will create a `date_inverted_index.json` file in the data directory used in next step.


----------
This part of README is in progress. Please ignore:

You will also be downloading data files from other services. Put these anywhere you want and make sure the importers point to the right place (there's always a variable at the top of the file with the pointer).



### GOOGLE PHOTOS
You need to download your Google photos from Google Takeout. I recommend to download the photos for a single year or two to start with. Otherwise, they shard the photos into multiple directories and it's a bit of a mess to deal with.

When downloaded, you'll get .json files (one for every photo) that has the meta-data about the photo and a photo file that has the photo itself. Note that there may be more json files than photos.

It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg

The easiest way to do this on a mac is:

 -- Select the .HEIC files you want to convert.
 -- Right click and choose "quick actions" and then you'll have an option to convert the image.
 -- If you're converting many photos, this may take a few minutes.

Put all the photos and all the json files in a folder called photos. The photos folder should be a sibling of the code folder.

### GOOGLE TIMELINE
Go to Google Takeout -- https://takeout.google.com/settings/takeout and ask to download your maps data.

### APPLE HEALTH
Got to the Apple Health app on your phone and ask to export your data. The will create a file called iwatch.xml and that's the input file to the importer.

### AMAZON
Request your data from Amazon here: https://www.amazon.com/gp/help/customer/display.html?nodeId=GXPU3YPMBZQRWZK2
They say it can take up to 30 days, but it took about 2 days. They'll send you an email when it's ready.

They separate purchases Amazon purchases from Kindle purchases into two different directories.

The file you need for Amazon purchases is Retail.OrderHistory.1.csv
The file you need for Kindle purchases is Digital Items.csv

Make sure the variables at the head of create_amazon_LLEntries.py point to the right files.

### SPOTIFY

Download your data from Spotify here -- https://support.spotify.com/us/article/data-rights-and-privacy-settings/
They say it can take up to 30 days, but it took about 2 days. They'll send you an email when it's ready.

The file you need is StreamingHistory0.json
Make sure the variable at the top of create_spotify_LLEntries.py points in the right place.

## Step 2: Running the offline enrichment and summarization pipeline

* Install all required packages (see above and `requirements.txt`).
* Register a Hugging Face account and request a Huggingface access token: [Link](https://huggingface.co/docs/hub/security-tokens)
```
export HF_TOKEN=<the token goes here>
```
* Fill in the user information in `user_info.json`, such as
```
{"name": "Hilbert", "address": "Menlo Park, California, United States"}
```

* Run:
```
python -m src.offline_processing
```

The script will generate 3 pickled indices: `activity_index.pkl`, `daily_index.pkl`, and `trip_index.pkl`.

An entry in the activity index looks like:
```
{ 'date': datetime.date(2018, 8, 30),
  'end_hour': 5,
  'num_photos': 4,
  'objects': { 'document': [ <some_paths_to_images> ]},
  'photo_summary': [ <some_paths_to_images> ],
  'start_hour': 5,
  'summary': 'A conference room, computer room, or conference center is full '
             'of people,.'}
```

An entry in the daily index looks like:
```
{ 'date': datetime.date(2018, 12, 9),
  'end_loc': 'San Jose;California;United States',
  'num_activities': 2,
  'num_photos': 4,
  'objects': { 'person': [ <some_paths_to_images> ]},
  'photo_summary': [ <some_paths_to_images> ],
  'start_loc': 'San Jose;California;United States',
  'summary': 'I spent today at San Jose.'}
```

An entry in the trip index looks like:
```
{ 'cities': ['Rio de Janeiro;Rio de Janeiro;Brasil'],
  'days': 3,
  'end_date': datetime.date(2018, 9, 1),
  'itinerary': [ { 'end': datetime.date(2018, 9, 1),
                   'location': 'Rio de Janeiro;Rio de Janeiro;Brasil',
                   'photo_summary': [ <some_paths_to_images> ],
                   'start': datetime.date(2018, 8, 29)}],
  'num_photos': 100,
  'start_date': datetime.date(2018, 8, 29),
  'summary': 'I went to Rio de Janeiro, Brazil, for 3 days in 2018/8.'}
```

## Step 3: Generate visualization

You need to first set up a Google Map API (free) following these [instructions](https://developers.google.com/maps/documentation/embed/quickstart#create-project).

```
export GOOGLE_MAP_API=<the API key goes here>
```

Run
```
python -m src.visualization
```

The script will generate a HTML page `index.html` for inspecting the timeline from your browser. Credit of the UI goes to [TimelineJS](https://timeline.knightlab.com/)!

<!-- #### Currently we use the BLIP package from Salesforce to generate captions.

Clone  https://github.com/salesforce/BLIP

Run:
    
    python -m src.get_captions



### APPLE HEALTH
Run:
    
    python -m code.create_apple_health_LLEntries.py

### AMAZON
Run:
    
    python -m code.create_amazon_LLEntries.py

### SPOTIFY

Run:

    python -m code.create_spotify_LLEntries.py -->

# CREATING THE LIFELOG (old version)

## Step 1: create an inverted index from date to all the entries from the different services.

Run 
    
    python -m src.create_index
Make sure that the variable DATA_DIR is the absolute path to the data directory.

## Step 2: Create the summary entries (daily, monthly, more to come)

In create_summary_LLEntries.py there's a variable with a list of cities that you consider home or around your home (hence, if you're there, you're not on a trip). Update that list to suit your situation. It's a hack -- we'll do it automatically at some point.

Run 

    python -m src.create_summary_LLEntries.py

# VISUALIZATION

install PySimpleGUI

Run 

    python -m src.timeline.py

Make sure the variable image_directory_path points to the directory with your photos.
