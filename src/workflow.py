from src.enrichment.geo_enrichment import LocationEnricher
# from src.enrichment.image_enrichment import ImageEnricher
from time import sleep

from src.export.export_entities import PhotoExporter
from src.importer.create_facebook_LLEntries import FacebookPhotosImporter
from src.importer.create_google_photo_LLEntries import GooglePhotosImporter

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
    print("Let's import some data first. What do you want to import?")
    #sleep(2)
    inp = input("1. Google Photos (data must be present in personal-data/google_photos) [y/n]? ").upper()
    action_arr.append("gp") if inp == 'Y' else None
    inp = input("2. Facebook Posts (data must be present in personal-data/facebook/posts) [y/n]? ").upper()
    action_arr.append("fp")  if inp == 'Y' else None
    # Enrich Location after import is complete
    inp = input("Should I run location enrichment [y/n]? ").upper()
    action_arr.append("geo_enrich") if inp == 'Y' else None
    inp = input("Should I run image enrichment [y/n]? ").upper()
    action_arr.append("image_enrich") if inp == 'Y' else None
    inp = input("Ok. Export all data in the end [y/n]? ").upper()
    action_arr.append("export") if inp == 'Y' else None

    if len(action_arr)==0:
        print("No new import task. Moving on...")
        #sleep(2)
    for action in action_arr:
        if action == "gp":
            # Do some basic validation of dirs
            #Import Google Photos
            print("Running Google photos import...")
            sleep(2)
            ip = GooglePhotosImporter()
            ip.start_import()
            print("Google Photos import complete")
            sleep(2)
        if action == "fp":
            # Do some basic validation of dirs
            #Import FB Photos
            print("Running FB Posts import...")
            sleep(2)
            i = FacebookPhotosImporter()
            i.start_import()
            print("FB Posts import complete")
            sleep(2)
        if action == 'geo_enrich':
            print("Running Location enrichment now...")
            sleep(2)
            le = LocationEnricher()
            le.enrich()
            print("Location enrichment complete")
        # if action == 'image_enrich':
        #     print("Running Image enrichment now...")
        #     sleep(2)
        #     le = ImageEnricher()
        #     le.enrich()
        #     print("Image enrichment complete")
        if action == 'export':
            print("Exporting enriched data to enriched_data...")
            sleep(2)
            ex = PhotoExporter()
            ex.create_export_entity()
            print("Export Complete. Finalized entities are now available in the DB under enriched_data column")
    print("Thanks for using the demo. See you Later, Gator!!!")
