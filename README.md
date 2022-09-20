This file explains how to create LifeLog entries from several data sources.


In the explanation, we'll assume three directories all sitting within the application directory:
  code, data, photos
  All code should be run in the code directory. Photos should be stored in the photos directory. The data directory will contain the json files that are created in the process of building the lifelog.

## Step 0: Create environment
    conda create pip --name <env> --file requirements.txt
    conda activate <env>
 * Note: There may be certain packages not available in conda. 
   Remove them from requirements.txt and install in the venv via pip after activation.

You will also be downloading data files from other services. Put these anywhere you want and make sure the importers point to the rigt place (there's always a variable at the top of the file with the pointer).

# GOOGLE PHOTOS
## Step 1: Downloading your photos

You need to download your Google photos from Google Takeout. I recommend to download the photos for a single year or two to start with. Otherwise, they shard the photos into multiple directories and it's a bit of a mess to deal with.

When downloaded, you'll get .json files (one for every photo) that has the meta-data about the photo and a photo file that has the photo itself. Note that there may be more json files than photos.

It may be the case that some of your photo files are .HEIC. In that case follow the steps below to convert them to .jpeg

The easiest way to do this on a mac is:

 -- Select the .HEIC files you want to convert.
 -- Right click and choose "quick actions" and then you'll have an option to covert the image.
 -- If you're converting many photos, this may take a few minutes.

Put all the photos and all the json files in a folder called photos. The photos folder should be a sibling of the code folder.

## Step 2: Generating captions

### Step 2.1: Find all the jpegs that also have json files (recall that Google doesn't always give you all the files onveniently in one folder, so this step is necessary to ensure that you have both the json and the .jpeg going forward)
    Run find_jpegs.py
    The output of find_jpegs.py will be photo_filenames.json

### Step 2.2: Generate the captions. Currently we use the BLIP package from Salesforce to generate captions.
          Clone  https://github.com/salesforce/BLIP
	  Run pip install -r requirements.txt
    Run get_captions.py
    The output of this step is photo_captions.json -- put that file in the ../data directory       

## Step 3: Create a json file with LLEntry for your photos (this is what will go into the episodic database).
    Run create_photo_LLEntries.py

# GOOGLE TIMELINE
Go to Google Takeout -- https://takeout.google.com/settings/takeout and ask to download your maps data.

APPLE HEALTH
Got to the Apple Health app on your phone and ask to export your data. The will create a file called iwatch.xml and that's the input file to the importer.

Run create_apple_health_LLEntries.py

# AMAZON
Request your data from Amazon here: https://www.amazon.com/gp/help/customer/display.html?nodeId=GXPU3YPMBZQRWZK2
They say it can take up to 30 days, but it took about 2 days. They'll send you an email when it's ready.

They separate purchases Amazon purchases from Kindle purchases into two different directories.

The file you need for Amazon purchases is Retail.OrderHistory.1.csv
The file you need for Kindle purchases is Digital Items.csv

Make sure the variables at the head of create_amazon_LLEntries.py point to the right files and run it.

# SPOTIFY

Download your data from Spotify here -- https://support.spotify.com/us/article/data-rights-and-privacy-settings/
They say it can take up to 30 days, but it took about 2 days. They'll send you an email when it's ready.

The file you need is StreamingHistory0.json
Make sure the variable at the top of create_spotify_LLEntries.py points in the right place and run it.

# CREATING THE LIFELOG

## Step 1: create an inverted index from date to all the entries from the different services.

Run create_index.py
Make sure that the variable DATA_DIR is the absolute path to the data directory.

## Step 2: Create the summary entries (daily, monthly, more to come)

In create_summary_LLEntries.py there's a variable with a list of cities that you consider home or around your home (hence, if you're there, you're not on a trip). Update that list to suit your situation. It's a hack -- we'll do it automatically at some point.

Run create_summary_LLEntries.py

# VISUALIZATION

install PySimpleGUI

Run timeline.py

Make sure the variable image_directory_path points to the directory with your photos.
