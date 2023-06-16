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
from enum import Enum

from src.common.objects.EntryTypes import EntryType
# Each element of this list is a dictionary with following attributes:
# Class Hierarchy:
# DataSourceList: list[
#   DataSource(
#       id: str                         ([Required] Unique source id.)
#       source_name: str                ([Required]: Name of the import source)
#       entry_type: src.common.objects.EntryTypes.EntryType ->
#                                       ([Required]: One of the allowed values from Enum EntryType)
#       configs: SourceConfigs(
#           input_directory = str       ([Required]: Directory containing data for this source)
#           filetype = str              ([Required]: xml/csv/json)
#           filename_regex = str        ([Optional]: regex for files)
#           filetype_configs = dict {
#               skiprows: int           ([Optional]: Used for CSV filetype for skipping
#                                                   first n rows of the csv. Defaults to 0)
#           }
#           dedup_key = str             ([Required]: List of attributes to use as composite key for
#                                                   deduplication when processing/re-processing data)
#       ),
#       field_mappings: list[           ([Required for config driven sources/
#                                         Optional for custom sources]:
#                                                   List containing mapping of field from input file to
#                                                   an attribute in LLEntry class.)
#           FieldMapping(
#               src: str                ([Required when mapping present]: Field name in input file)
#               target: str             ([Required when mapping present]: Attribute name in LLEntry class)
#               src_type: str           ([Required when mapping present]: Data type of field in Source
#                                                    Possible values: str, dict, datetime, number, not tested fully)
#               target_type: str        ([Required when mapping present]: Data type of attribute in LLEntry class
#                                                    Possible values: str, dict, datetime, number, not tested fully))
#               default_value: str      ([Optional]: Value to store when data is absent.
#                                                    Values default to None if default_value is not provided)
#               functions: list         ([Optional]: Function to evaluate to convert source value to target value.
#                                                    Since this list is parsed in sequence, this function has access
#                                                    to mappings already done. As such, it can work on the src,
#                                                    as well as already mapped target attributes. FOr usage refer to
#                                                    data_source.json and evaluate_functions in
#                                                    [generic_importer.py](src/ingest/importers/generic_importer.py)
#           )
#       ]
#   )
# ]
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
                 filename_regex:str, filetype_configs:dict,
                 dedup_key: list):
        self.input_directory = input_directory
        self.filetype = filetype
        self.filename_regex = filename_regex
        self.filetype_configs = filetype_configs
        self.dedup_key = dedup_key

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
                                     get_val_or_none(configs, "filetype_configs"),
                                     get_val_or_none(configs, "dedup_key"))
        self.field_mappings = []
        if field_mappings is not None:
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