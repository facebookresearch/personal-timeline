# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
import pickle
import logging as log

from src.ingest.importers.create_facebook_LLEntries import FacebookPhotosImporter
from src.ingest.importers.create_google_photo_LLEntries import GooglePhotosImporter
from src.ingest.importers.create_googlemaps_LLEntries import GoogleMapsImporter
from src.ingest.importers.create_apple_health_LLEntries import AppleHealthImporter
from src.ingest.importers.generic_importer import SimpleJSONImporter, CSVImporter
from src.common.objects.import_configs import DataSourceList, SourceConfigs, FileType
from src.common.persistence.personal_data_db import PersonalDataDBConnector


class GenericImportOrchestrator:
    def __init__(self):
        self.pdc = PersonalDataDBConnector()
        self.import_greenlit_sources = []

    def add_new_source(self, datasource: DataSourceList):
        # TODO: Insert new entry to Data Source
        datasource.__dict__

    def start_import(self):
        existing_sources = self.pdc.read_data_source_conf("id, source_name, entry_type, configs, field_mappings")
        if existing_sources is not None:
            for source in existing_sources:
                source_id = source[0]
                source_name = source[1]
                entry_type = source[2]
                configs: SourceConfigs = pickle.loads(source[3])
                field_mappings: list = pickle.loads(source[4])
                log.info(f"Configurations found for {source_name}. "
                         f"Attempting to import data from {configs.input_directory}")
                imp=None
                if source_name == "GoogleTimeline":
                    imp = GoogleMapsImporter(source_id, source_name, entry_type, configs)
                elif source_name == "GooglePhotos":
                    imp = GooglePhotosImporter(source_id, source_name, entry_type, configs)
                elif source_name == "FacebookPosts":
                    imp = FacebookPhotosImporter(source_id, source_name, entry_type, configs)
                elif source_name == "AppleHealth" and configs.filetype == FileType.XML:
                    imp = AppleHealthImporter(source_id, source_name, entry_type, configs)
                elif configs.filetype == FileType.JSON:
                    imp = SimpleJSONImporter(source_id, source_name, entry_type, configs)
                elif configs.filetype == FileType.CSV:
                    imp = CSVImporter(source_id, source_name, entry_type, configs)
                print("Beginning import for", imp.source_name)
                imp.import_data(field_mappings)
        else:
            log.info("No Data source registered with importers.")

    def import_from_xml(self, source_name: str, configs: SourceConfigs, field_mappings: list):
        print("XML")
