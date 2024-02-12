# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import json
import os

from src.common.persistence.personal_data_db import PersonalDataDBConnector
from src.ingest.enrichment.geo_enrichment import LocationEnricher
from src.ingest.enrichment.image_enrichment import ImageEnricher

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
    gip = GenericImportOrchestrator()
    if os.getenv("ingest_new_data") is not None and os.environ["ingest_new_data"] != ''\
            and os.environ["ingest_new_data"] == "True":
        print("Ingest new Data is set to true")
        gip.start_import()
    # Enrich Location after import is complete
    action_arr.append("geo_enrich")
    action_arr.append("image_enrich")
    action_arr.append("export")
    if len(action_arr)==0:
        print("No new import task.")
    for action in action_arr:
        if action == 'geo_enrich':
            print("Running Location enrichment now...")
            le = LocationEnricher()
            if os.getenv("incremental_geo_enrich") is not None and os.environ["incremental_geo_enrich"]!='':
                geoenrich_increments = True if os.environ["incremental_geo_enrich"] == "True" else False
                le.enrich(geoenrich_increments)
            else:
                le.enrich()
            print("Location enrichment complete")
        if action == 'image_enrich':
            print("Running Image enrichment now...")
            # sleep(2)
            le = ImageEnricher()
            if os.getenv("incremental_image_enrich") is not None and os.environ["incremental_image_enrich"]!='':
                image_enrich_increments = True if os.environ["incremental_image_enrich"] == "True" else False
                le.enrich(image_enrich_increments)
            else:
                le.enrich()
            print("Image enrichment complete")
        if action == 'export':
            print("Exporting enriched data to enriched_data...")
            ex = PhotoExporter()
            if os.getenv("incremental_export") is not None and os.environ["incremental_export"]!='':
                export_increments = True if os.environ["incremental_export"] == "True" else False
                print("Incremental Export flag is set to ", export_increments)
                ex.create_export_entity(export_increments)
            else:
                ex.create_export_entity()
            print("Merge Complete. Enriched entities pushed to enriched_data column")
            # if os.getenv("export_enriched_data_to_json") is not None\
            #         and os.environ["export_enriched_data_to_json"] == "True":
            if os.getenv("enriched_data_to_json") is not None\
                    and os.environ["enriched_data_to_json"] == "True":
                export_path = os.path.join(os.environ["APP_DATA_DIR"], 'enriched_data.json')
                json.dump(ex.get_all_data(), open(export_path, "w"))
                print("Data exported as json to", export_path)

    # Print Import Summary
    print("------------------------------------------------")
    print("--------------Data Stats By Source--------------")
    print("------------------------------------------------")
    PersonalDataDBConnector().print_data_stats_by_source()
    print("--------------Data Import Complete--------------")