This file explains how to create LifeLog entries from your Google photos.

In the explanation, we'll assume three directories all sitting within the application directory:
  code, data, photos
 All code should be run in the code directory

## Step 0: Create environment
    conda create --name <env> --file requirements.txt
    conda activate

## Step 1: Downloading your photos

You need to download your Google photos from Google Takeout. I recommend to download the photos for a single year or two to start with. Otherwise, they shard the photos into multiple directories and it's a bit of a mess to deal with.

When downloaded, you'll get .json files (one for every photo) that has the meta-data about the photo and an .HEIC file that has the photo itself. Note that there may be more json files than photos.

.HEIC files are not very useful, so you need to turn them into .jpeg. The easiet way to do this on a mac is:

 -- Select the .HEIC files you want to convert.
 -- Right click and choose "quick actions" and then you'll have an option to covert the image.
 -- If you're converting many photos, this may take a few minutes.

Put all the photos and all the json files in a folder called photos. The photos folder should be a sibling of the code folder.

## Step 2: Generating captions

### Step 2.1: Find all the jpegs that also have json files (recall that Google doesn't always give you all the files onveniently in one folder, so this step is necessary to ensure that you have both the json and the .jpeg going forward)
Run find_jpegs.py
The output of find_jpegs.py will be photo_filenames.json

### Step 2.2: Generate the captions
Run get_captions.py
The output of this step is photo_captions.json -- put that file in the ../data directory       

## Step 3: Create a json file with LLEntry for your photos (this is what will go into the episodic database).
Run create_photo_LLEntries.py
