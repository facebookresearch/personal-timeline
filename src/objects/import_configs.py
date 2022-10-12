import json
from enum import Enum

from src.objects.EntryTypes import EntryType


def get_val_or_none(kv:dict, key:str):
    if key in kv.keys():
        return kv[key]
    else:
        return None

class FileType(str, Enum):
    CSV: str="csv"
    JSON: str="json"
    XML: str="xml"

    def toJson(self):
        return json.dumps(self.__dict__.values())

class SourceConfigs:
    def __init__(self, input_directory:str, filetype:FileType,
                 filename_regex:str, filetype_configs:dict):
        self.input_directory = input_directory
        self.filetype = filetype
        self.filename_regex = filename_regex
        self.filetype_configs = filetype_configs

    def __str__(self):
        return self.input_directory + " " + self.filetype

    def toJson(self):
        return json.dumps(self.__dict__)


class FieldMapping:
    def __init__(self,src, target, src_type, target_type, functions, default_value=""):
        self.src: str = src
        self.target: str = target
        self.src_type: str = src_type
        self.target_type: str = target_type
        self.default_value: str = default_value
        self.functions: list = functions

    def __str__(self):
        return self.src + " " + self.target + " " + self.src_type + " " + self.target_type

    def toJson(self):
        return json.dumps(self.__dict__)


class DataSource:
    def __init__(self, id, source_name, entry_type:EntryType, configs, field_mappings):
        self.id: int = id
        self.source_name: str = source_name
        self.entry_type = entry_type


        self.configs = SourceConfigs(get_val_or_none(configs, "input_directory"),
                                     get_val_or_none(configs, "filetype"),
                                     get_val_or_none(configs, "filename_regex"),
                                     get_val_or_none(configs, "filetype_configs"))
        self.field_mappings = []
        for f in field_mappings:
            self.field_mappings.append(FieldMapping(get_val_or_none(f, "src"),
                                                    get_val_or_none(f, "target"),
                                                    get_val_or_none(f, "src_type"),
                                                    get_val_or_none(f, "target_type"),
                                                    get_val_or_none(f, "functions"),
                                                    get_val_or_none(f, "default_value")))

    def __str__(self):
        return str(self.id) + " " + self.source_name + " " + self.configs.__str__() + \
               " " + self.field_mappings.__str__()

    def toJson(self):
        return json.dumps(self.__dict__)

class DataSourceList:
    def __init__(self, ds):
        self.data_sources = []
        for entry in ds:
            entry_type:EntryType = get_val_or_none(entry, "entry_type")
            if entry_type is None:
                raise Exception("Entry Type cannot be null for data source " + get_val_or_none(entry, "source_name"))
            self.data_sources.append(DataSource(get_val_or_none(entry, "id"),
                                                get_val_or_none(entry, "source_name"),
                                                get_val_or_none(entry, "entry_type"),
                                                get_val_or_none(entry, "configs"),
                                                get_val_or_none(entry, "field_mappings")))

    def __str__(self):
        return self.data_sources.__str__()

    def toJson(self):
        return json.dumps(self.__dict__)