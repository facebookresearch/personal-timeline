This file explains how to create LifeLog entries from several data sources.


In the explanation, we'll assume three directories all sitting within the application directory:
  code, data, photos
  All code should be run in the code directory. Photos should be stored in the photos directory. The data directory will contain the json files that are created in the process of building the lifelog.

# Step 0: Create environment

1. Install Docker Desktop from [this link](https://docs.docker.com/desktop/).

2. Follow install steps and use the Desktop app to start the docker engine.

3. Create a new directory under your home folder (this is where all your personal-data will be downloaded)  
    ```$ mkdir ~/personal-data```

4. Create environment file
    ```$ touch env.list```

5. Register a Hugging Face account and request a Huggingface access token: [Link](https://huggingface.co/docs/hub/security-tokens)
    Add the following line to the `env.list` file:
    ```
   HF_TOKEN=<the token goes here>
    ```
* Fill in the user information in `user_info.json`, such as (keeping the previous ``address`` for backward compatibility)
```
{
    "name": "Hilbert",
    "address": "Menlo Park, California, United States",
    "addresses": [
        {
            "name": "Work",
            "address": "Menlo Park, California, United States",
            "radius": 0.1
        },
        {
            "name": "Home",
            "address": "Menlo Park, California, United States",
            "radius": 0.1
        },
        {
            "name": "My neighborhood",
            "address": "Menlo Park, California, United States",
            "radius": 1
        }

    ]
}
```

# Step 1: Downloading your photos

### GOOGLE PHOTOS
1. You need to download your Google photos from [Google Takeout](https://takeout.google.com/).  
The download from Google Takeout would be in multiple zip files. Unzip all the files.

<!-- 2. It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg  
The easiest way to do this on a Mac is:

     -- Select the .HEIC files you want to convert.   
     -- Right click and choose "quick actions" and then you'll have an option to convert the image.  
     -- If you're converting many photos, this may take a few minutes. -->
2. Create a new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/google_photos```
3. Move all the unzipped folders inside `personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.

### FACEBOOK DATA
1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=your_facebook_information) 
2. Click on <b>Download your information</b> and download FB data in JSON format
3. Create a new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/facebook```
3. Unzip the downloaded file and copy the directory `posts` sub-folder to the above folder. The `posts` folder would sit directly under the facebook folder.

### APPLE HEALTH
1. Go to the Apple Health app on your phone and ask to export your data. This will create a file called iwatch.xml and that's the input file to the importer.
2. Create a new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/apple-health```
3. Move the downloaded file to this folder.  

### AMAZON
1. Request your data from Amazon here: https://www.amazon.com/gp/help/customer/display.html?nodeId=GXPU3YPMBZQRWZK2
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

They separate Amazon purchases from Kindle purchases into two different directories.

The file you need for Amazon purchases is Retail.OrderHistory.1.csv
The file you need for Kindle purchases is Digital Items.csv

2. Create two new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/amazon```  
    ```$ mkdir ~/personal-data/amazon-kindle```

3. Move data for amazon purchases to `amazon` folder and of kindle downloads to `amazon-kindle` folder

### SPOTIFY

1. Download your data from Spotify here -- https://support.spotify.com/us/article/data-rights-and-privacy-settings/
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

2. Create two new directory under `personal-data` folder  
    ```$ mkdir ~/personal-data/spotify``` 

3. Move the data into this folder.

# Step 2: Import your photo data to SQLite (this is what will go into the episodic database) and build summaries

1. Build docker image
    ```docker build -t pd-importer .```

2. Run docker container
    ```docker run -it --entrypoint bash -v ~/personal-data/:/app/personal-data/ pd-importer```
    This will give you access to the container's shell with access to personal-data directory.
   (Note: Above command is for Mac. Path for mounting Volume may be a bit different for Windows)  

3. Inside the docker image shell, run the following command:
```python -m src.workflow```

The script will allow you to choose the steps you want to run from the workflow.  
Follow the instructions to import and enrich data. 

(Note: please select `No` for image enrichment for now. It is currently implemented within the `offline_processing.py` step.)
(Note*: please select `Yes` at the last step for exporting the LLEntries.)

The script will add two types of file to `~/personal-data/app_data` folder 
 - Import your data to an SQLite format file named `raw_data.db`
 - Generate 3 pickled indices: `activity_index.pkl`, `daily_index.pkl`, and `trip_index.pkl`. 
    (See the `LLEntrySummary` class in `src/objects/LLEntry_obj.py` the object class definitions.)
    


# Step 4: Generate visualization

You need to first set up a Google Map API (free) following these [instructions](https://developers.google.com/maps/documentation/embed/quickstart#create-project).

```
export GOOGLE_MAP_API=<the API key goes here>
```

To embed Spotify, you need to set up a Spotify API (free) following [here](https://developer.spotify.com/dashboard/applications). You need to log in with a spotify account, create a project, and show the `secret`.

```
export SPOTIFY_TOKEN=<the token goes here>
export SPOTIFY_SECRET=<the secret goes here>
```

If you have previously created some cached images in `images/`, rename it to `static/`
```
mv images/ static/
```

Run
```
python server.py
```

It will start a flask server at `http://127.0.0.1:5000`. You can view the timeline this link. Credit of the UI goes to [TimelineJS](https://timeline.knightlab.com/)!

You can also search the timeline with queries :).

<!--
# Step 6: Running the interactive GUI (WIP)

Make sure that you have installed QT from `requirements.txt`. Launch the interactive GUI:

```
python -m src.gui.main
```

Now you can search the timeline with queries!

#### Currently we use the BLIP package from Salesforce to generate captions.

----------
This part of README is in progress. Please ignore:

You will also be downloading data files from other services. Put these anywhere you want and make sure the importers point to the right place (there's always a variable at the top of the file with the pointer).

### GOOGLE TIMELINE
Go to Google Takeout -- https://takeout.google.com/settings/takeout and ask to download your maps data.

Clone  https://github.com/salesforce/BLIP

Run:
    
    python -m src.get_captions



### APPLE HEALTH
Run:
    
    python -m code.create_apple_health_LLEntries.py


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

Make sure the variable image_directory_path points to the directory with your photos. -->
