import os

from src.common.persistence.personal_data_db import PersonalDataDBConnector
from src.ingest.enrichment.geo_enrichment import LocationEnricher
# from src.enrichment.image_enrichment import ImageEnricher

from src.ingest.export.export_entities import PhotoExporter
from src.ingest.importers.generic_importer_workflow import GenericImportOrchestrator

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
    print("--------------Data Import Start--------------")
    # print("Let's begin. Press [n] at anytime to break")
    # inp = input("1. Google Photos (data must be present in personal-data/google_photos) [y/n]? ").upper()
    # action_arr.append("gp") if inp == 'Y' else None
    # inp = input("2. Facebook Posts (data must be present in personal-data/facebook/posts) [y/n]? ").upper()
    # action_arr.append("fp")  if inp == 'Y' else None
    gip = GenericImportOrchestrator()
    # Enrich Location after import is complete
    # inp = input("Should I run location enrichment on entities [y/n]? ").upper()
    action_arr.append("geo_enrich") # if inp == 'Y' else None
    # inp = input("Should I run image enrichment [y/n]? ").upper()
    action_arr.append("image_enrich") # if inp == 'Y' else None
    # inp = input("Merge enrichments to raw data in the end [y/n]? ").upper()
    action_arr.append("export") # if inp == 'Y' else None
    if len(action_arr)==0:
        print("No new import task.")
    gip.start_import()
    for action in action_arr:
        if action == 'geo_enrich':
            print("Running Location enrichment now...")
            if os.environ["incremental_geo_enrich"] is not None and os.environ["incremental_geo_enrich"]!='':
                geoenrich_increments = os.environ["incremental_geo_enrich"]
            print("Incremental Geo Enrich flag is set to ", geoenrich_increments)
            le = LocationEnricher()
            le.enrich(geoenrich_increments)
            print("Location enrichment complete")
        # if action == 'image_enrich':
        #     print("Running Image enrichment now...")
        #     sleep(2)
        #     le = ImageEnricher()
        #     le.enrich()
        #     print("Image enrichment complete")
        if action == 'export':
            print("Exporting enriched data to enriched_data...")
            ex = PhotoExporter()
            if os.environ["incremental_export"] is not None and os.environ["incremental_export"]!='':
                export_increments = os.environ["incremental_export"]
            print("Incremental Export flag is set to ", export_increments)
            ex.create_export_entity(export_increments)
            print("Merge Complete. Full photo entities are available in enriched_data column")
    # Print Import Summary
    print("------------------------------------------------")
    print("--------------Data Stats By Source--------------")
    print("------------------------------------------------")
    PersonalDataDBConnector().print_data_stats_by_source()
    print("--------------Data Import Complete--------------")