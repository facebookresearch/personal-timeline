import pickle
import os
from pathlib import Path
import json

from src.importer.all_importer import SimpleJSONImporter, CSVImporter
from src.objects.import_configs import DataSourceList, SourceConfigs, FileType
from src.persistence.personal_data_db import PersonalDataDBConnector


class GenericImportOrchestrator:
    def __init__(self):
        # input_dir = str(Path("personal-data/venmo").absolute())
        self.pdc = PersonalDataDBConnector()
        self.pdc.setup_tables()
        self.import_greenlit_sources = []

    def seek_user_consent(self):
        existing_sources = self.pdc.read_data_source_conf("id, source_name, configs")
        if existing_sources is not None:
            for source in existing_sources:
                id = source[0]
                source_name = source[1]
                conf = pickle.loads(source[2])
                print("Configurations found for ", source_name)
                print("Configs: ", conf.__dict__)
                uinput = input("Import data for " + source_name + " [y/n]? ")
                if uinput.lower() == 'y':
                    self.import_greenlit_sources.append(source_name)
        else:
            print("No Data source registered with importer.")

    def add_new_source(self, datasource: DataSourceList):
        # TODO: Insert new entry to Data Source
        datasource.__dict__

    def start_import(self):
        if len(self.import_greenlit_sources) == 0:
            print("No generic imports scheduled.")
        else:
            for source in self.import_greenlit_sources:
                result = self.pdc.read_data_source_conf("source_name, entry_type, configs, field_mappings", source)
                if len(result) == 1:
                    source_name = result[0][0]
                    entry_type = result[0][1]
                    configs: SourceConfigs = pickle.loads(result[0][2])
                    field_mappings: list = pickle.loads(result[0][3])
                    print("Configs for ", source_name, ": ")
                    print(configs.__dict__)
                    print(field_mappings)
                    imp=None
                    if configs.filetype == FileType.JSON:
                        imp = SimpleJSONImporter(source_name, entry_type)
                    elif configs.filetype == FileType.CSV:
                        imp = CSVImporter(source_name, entry_type)  # TODO CSV
                    # elif configs.filetype == FileType.XML:
                    #     imp = XMLImporter(source_name, entry_type) #TODO XML
                    imp.import_data(configs, field_mappings)

    def import_from_xml(self, source_name: str, configs: SourceConfigs, field_mappings: list):
        print("XML")
