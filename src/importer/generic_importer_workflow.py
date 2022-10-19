import pickle

from src.create_googlemaps_LLEntries import GoogleMapsImporter
from src.importer.create_apple_health_LLEntries import AppleHealthImporter
from src.importer.all_importers import SimpleJSONImporter, CSVImporter
from src.objects.import_configs import DataSourceList, SourceConfigs, FileType
from src.persistence.personal_data_db import PersonalDataDBConnector


class GenericImportOrchestrator:
    def __init__(self):
        self.pdc = PersonalDataDBConnector()
        self.pdc.setup_tables()
        self.import_greenlit_sources = []

    def seek_user_consent(self):
        existing_sources = self.pdc.read_data_source_conf("id, source_name, configs")
        if existing_sources is not None:
            for source in existing_sources:
                id = source[0]
                source_name = source[1]
                conf:SourceConfigs = pickle.loads(source[2])
                print("Configurations found for ", source_name)
                #print("Configs: ", conf.__dict__)
                uinput = input("Import data for " + source_name + " from '"+ conf.input_directory +"' [y/n]? ")
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
                result = self.pdc.read_data_source_conf("id, source_name, entry_type, configs, field_mappings", source)
                if len(result) == 1:
                    source_id = result[0][0]
                    source_name = result[0][1]
                    entry_type = result[0][2]
                    configs: SourceConfigs = pickle.loads(result[0][3])
                    field_mappings: list = pickle.loads(result[0][4])
                    #print("Configs for ", source_name, ": ")
                    #print(configs.__dict__)
                    #print(field_mappings)
                    imp=None
                    if source_name == "GoogleTimeline":
                        imp = GoogleMapsImporter(source_id, source_name, entry_type, configs)
                    elif configs.filetype == FileType.JSON:
                        imp = SimpleJSONImporter(source_id, source_name, entry_type, configs)
                    elif configs.filetype == FileType.CSV:
                        imp = CSVImporter(source_id, source_name, entry_type, configs)  # TODO CSV
                    elif configs.filetype == FileType.XML and source_name=="AppleHealth":
                        imp = AppleHealthImporter(source_id, source_name, entry_type, configs) #TODO XML
                    imp.import_data(field_mappings)

    def import_from_xml(self, source_name: str, configs: SourceConfigs, field_mappings: list):
        print("XML")
