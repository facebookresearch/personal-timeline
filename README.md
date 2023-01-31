This file explains how to create LifeLog entries from several data sources.


In the explanation, we'll assume three directories all sitting within the application directory:
  code, data, photos
  All code should be run in the code directory. Photos should be stored in the photos directory. The data directory will contain the json files that are created in the process of building the lifelog.

# Step 0: Create environment

1. Install Docker Desktop from [this link](https://docs.docker.com/desktop/).

2. Follow install steps and use the Desktop app to start the docker engine.

3. Run init script
    ```
    sh src/init.sh
    ```
This will create a bunch of files/folders/symlinks needed for running the app.
This will also create a new directory under your home folder `~/personal-data`, the directory where your personal data will reside.

# Step 1: General Setup
## For Data Ingestion
1. Register a Hugging Face account and request a Huggingface access token: [Link](https://huggingface.co/docs/hub/security-tokens)
    Add the following line to the `env/ingest.env.list` file:
    ```
   HF_TOKEN=<the token goes here>
    ```
2. Fill in the user information in `user_info.json`, such as (keeping the previous ``address`` for backward compatibility)
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
3. Ingestion configs are controlled via parameters in `conf/ingest.conf` file. The configurations
are defaulted for optimized processing and don't need to be changed. 
You can adjust values for these parameters to run importer with a different configuration.

## For Data visualization

1. To set up a Google Map API (free), follow these [instructions](https://developers.google.com/maps/documentation/embed/quickstart#create-project).

Copy the following lines to `env/frontend.env.list`:
```
GOOGLE_MAP_API=<the API key goes here>
```

2. To embed Spotify, you need to set up a Spotify API (free) following [here](https://developer.spotify.com/dashboard/applications). You need to log in with a spotify account, create a project, and show the `secret`.

Copy the following lines to `env/frontend.env.list`:
```
SPOTIFY_TOKEN=<the token goes here>
SPOTIFY_SECRET=<the secret goes here>
```


# Step 2: Downloading your personal data

We currently supports 9 data sources. Here is a summary table:

| Digital Services | Instructions                                                                        | Destinations                                                             | Use cases                                              |
|------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------|
| Apple Health     | [Link](https://github.com/alonhalevy/personal-timeline#apple-health)  | personal-data/apple-health                                               | Exercise patterns, calorie counts                      |
| Amazon           | [Link](https://github.com/alonhalevy/personal-timeline#amazon)        | personal-data/amazon                                                     | Product recommendation, purchase history summarization |
| Amazon Kindle    | [Link](https://github.com/alonhalevy/personal-timeline#amazon)        | personal-data/amazon-kindle                                              | Book recommendation                                    |
| Spotify          | [Link](https://github.com/alonhalevy/personal-timeline#spotify)       | personal-data/spotify                                                    | Music / streaming recommendation                       |
| Venmo            | [Link](https://github.com/alonhalevy/personal-timeline#venmo)         | personal-data/venmo                                                      | Monthly spend summarization                            |
| Libby            | [Link](https://github.com/alonhalevy/personal-timeline#libby)         | personal-data/libby                                                      | Book recommendation                                    |
| Google Photos    | [Link](https://github.com/alonhalevy/personal-timeline#google-photos) | personal-data/google_photos                                              | Food recommendation, Object detections, and more               |
| Google Location  | [Link](https://github.com/alonhalevy/personal-timeline#google-photos) | personal-data/google-timeline/Location History/Semantic Location History | Location tracking / visualization                      |
| Facebook posts   | [Link](https://github.com/alonhalevy/personal-timeline#facebook-data) | personal-data/facebook                                                   | Question-Answering over FB posts / photos              |

### GOOGLE PHOTOS and Timeline
<!--1. You need to download your Google photos from [Google Takeout](https://takeout.google.com/).  
The download from Google Takeout would be in multiple zip files. Unzip all the files.

2. It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg  
The easiest way to do this on a Mac is:

     -- Select the .HEIC files you want to convert.   
     -- Right click and choose "quick actions" and then you'll have an option to convert the image.  
     -- If you're converting many photos, this may take a few minutes. 

2. Move all the unzipped folders inside `~/personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.-->

1. You can download your Google photos and location (also gmail, map and google calendar) data from [Google Takeout](https://takeout.google.com/).
2. The download from Google Takeout would be in multiple zip files. Unzip all the files.
3. For Google photos, move all the unzipped folders inside `~/personal-data/google_photos/`. There can be any number of sub-folders under `google_photos`.
4. For Google locations, move the unzipped files to `personal-data/google-timeline/Location History/Semantic Location History`.

### FACEBOOK DATA
1. Go to [Facebook Settings](https://www.facebook.com/settings?tab=your_facebook_information) 
2. Click on <b>Download your information</b> and download FB data in JSON format
3. Unzip the downloaded file and copy the directory `posts` sub-folder to `~/personal-data/facebook`. The `posts` folder would sit directly under the facebook folder.

### APPLE HEALTH
1. Go to the Apple Health app on your phone and ask to export your data. This will create a file called iwatch.xml and that's the input file to the importer.
2. Move the downloaded file to this `~/personal-data/apple-health`

### AMAZON
1. Request your data from Amazon here: https://www.amazon.com/gp/help/customer/display.html?nodeId=GXPU3YPMBZQRWZK2
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

They separate Amazon purchases from Kindle purchases into two different directories.

The file you need for Amazon purchases is Retail.OrderHistory.1.csv
The file you need for Kindle purchases is Digital Items.csv

2. Move data for amazon purchases to `~/personal-data/amazon` folder and of kindle downloads to `~/personal-data/amazon-kindle` folder

### Venmo
1. Download your data from Venmo here -- https://help.venmo.com/hc/en-us/articles/360016096974-Transaction-History

2. Move the data into `~/personal-data/venmo` folder.

### Libby
1. Download your data from Libby here -- https://libbyapp.com/timeline/activities. Click on `Actions` then `Export Timeline`

2. Move the data into `~/personal-data/libby` folder.


### SPOTIFY

1. Download your data from Spotify here -- https://support.spotify.com/us/article/data-rights-and-privacy-settings/
They say it can take up to 30 days, but it took about 2 days. They'll email you when it's ready.

2. Move the data into `~/personal-data/spotify` folder.

# Step 3: Running the code
Now that we have all the data and setting in place, we can either run individual steps or the end-to-end system.
This will import your photo data to SQLite (this is what will go into the episodic database), build summaries
and make data available for visualization and search.


Running the Ingestion container will add two types of file to `~/personal-data/app_data` folder
 - Import your data to an SQLite format file named `raw_data.db`
 - Generate 3 pickled indices: `activity_index.pkl`, `daily_index.pkl`, and `trip_index.pkl`. 
    (See the `LLEntrySummary` class in `src/objects/LLEntry_obj.py` the object class definitions.)

### Option 1:
To run the pipeline end-to end(both frontend and backend), simply run 
```
docker-compose up -d
```

### Option 2:
You can also run ingestion and visualization separately.
To start data ingestion, use  
```
docker-compose up -d backend
```  
To start visualization
```
docker-compose up -d frontend
```

# Step 4: Check progress
Once the docker command is run, you can see running containers for backend and frontend in the docker for Mac UI.
Copy the container Id for ingest and see logs by running the following command:  
```
docker logs -f <container_id>
```

# Step 5: Visualization

Running the Frontend will start a flask server inside a docker container at `http://127.0.0.1:5000`. 
You can view the timeline via this link. Credit of the UI goes to [TimelineJS](https://timeline.knightlab.com/)!
* Note: Accessing UI via `http://localhost:5000` does not render the timeline due to some CORS Policy restrictions. 
Make sure you are using `127.0.0.1` as prescribed.
