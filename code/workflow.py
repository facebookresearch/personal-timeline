from code.enrichment.geo_enrichment import LocationEnricher
from time import sleep

from code.export.export_entities import PhotoExporter
from code.importer.create_facebook_LLEntries import FacebookPhotosImporter
from code.importer.create_google_photo_LLEntries import GooglePhotosImporter

# Workflow is as follows:
# After data is downloaded in respective folders:
# For photos:
# 1. Generate Captions for images
# 2. Run import to generate input entity (takes caption as input)
# 3. Run enrichment functions (geo, image_dedup etc.)
# 4. Export to daily index -> Some Storage TBD
# 5. Generate Summaries -> Some Storage TBD
if __name__ == '__main__':
    action_arr = []
    print("Welcome to the demo!!!")
    #sleep(2)
    print("Let's import some data first. What do you want to import?")
    #sleep(2)
    in1 = input("1. Google Photos (data must be present in photos/google_photos) [y/n]? ").upper()
    action_arr.append("1") if in1 == 'Y' else None
    in2 = input("2. Facebook Posts (data must be present in photos/facebook/posts) [y/n]? ").upper()
    action_arr.append("2")  if in2 == 'Y' else None

    if len(action_arr)==0:
        print("No new import task. Moving on...")
        #sleep(2)
    for action in action_arr:
        if action == "1":
            # Do some basic validation of dirs
            #Import Google Photos
            ip = GooglePhotosImporter()
            ip.start_import()
            print("Google Photos import complete")
            sleep(2)
        if action == "2":
            # Do some basic validation of dirs
            #Import FB Photos
            i = FacebookPhotosImporter()
            i.start_import()
            print("FB Posts import complete")
            sleep(2)

    #Enrich Location after import is complete
    print("Running Location enrichments now...")
    sleep(2)
    le = LocationEnricher()
    le.enrich()

    in3 = input("Run export [y/n]? ").upper()
    if in3 == 'Y':
        ex = PhotoExporter()
        ex.create_export_entity()
        print("Export Complete. Finalized entities are now available in the DB")

    print("Thanks for using the demo!!!")