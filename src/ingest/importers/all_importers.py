import json
import pickle
import re
from abc import abstractmethod
from pathlib import Path
import os
import pandas as pd
from tqdm import tqdm

from src.common.objects.EntryTypes import EntryType
from src.common.objects.LLEntry_obj import LLEntry
from src.common.objects.import_configs import SourceConfigs, FieldMapping
import parsedatetime
#Keep imports that may be used in dynamic function evaluation
from datetime import datetime, timedelta

from src.common.persistence.personal_data_db import PersonalDataDBConnector


class GenericImporter:
    def __init__(self, source_id:int, source_name:str, entry_type:EntryType, configs:SourceConfigs):
        self.pdc = PersonalDataDBConnector()
        self.source_id = source_id
        self.source_name = source_name
        self.entry_type = entry_type
        self.configs = configs
        self.cal = parsedatetime.Calendar()

    @abstractmethod
    def import_data(self, field_mappings:list):
        pass

    def get_type_files_deep(self, pathname: str, filename_pattern: str, type: list) -> list:
        json_files = []
        type_str: str = "|".join(type).lower()
        if filename_pattern is None:
            filename_regex = ".*"
        else:
            filename_regex = ".*" + filename_pattern.lower() + ".*"
        if os.path.isdir(pathname):
            dir_entries = os.listdir(pathname)
            for dir_entry in dir_entries:
                all_json = self.get_type_files_deep(pathname + "/" + dir_entry, filename_pattern, type)
                if all_json is not None:
                    if isinstance(all_json, list):
                        for one_json in all_json:
                            json_files.append(one_json)
                    else:
                        json_files.append(all_json)
            return json_files
        elif os.path.isfile(pathname) \
                and re.match(filename_regex + "\.(" + type_str + ")$", pathname.lower()):
            path_arr = []
            path_arr.append(pathname)
            return path_arr

    def build_db_entry(self, obj: LLEntry):
        db_entry = {}
        dedup_value = self.build_dedup_value(obj, self.configs.dedup_key)
        # id, source_id, data_timestamp, dedup_key, data
        db_entry["source_id"] = self.source_id
        db_entry["data_timestamp"] = obj.startTime
        db_entry["dedup_key"] = dedup_value
        db_entry["data"] = obj
        return db_entry
    def build_dedup_value(self, obj: LLEntry, unique_key:list):
        dedup_key = ""
        for attrib in unique_key:
            if obj.__getattribute__(attrib) is not None:
                dedup_key+=str(obj.__getattribute__(attrib))+"_"
            else:
                dedup_key+="__"
        return dedup_key[:-1]
    def create_LLEntry(self, row:dict, field_mappings:list):
        lifelog_obj = LLEntry(self.entry_type, "", self.source_name)
        for fmp in field_mappings:
            field_mapping:FieldMapping = fmp
            ll_attrib_name = field_mapping.target
            ll_attribe_type = field_mapping.target_type
            if field_mapping.src is not None:
                if field_mapping.src in row.keys():
                    src_value = row[field_mapping.src]
                    #When a function is applied over source data before aading to llentry
                    if field_mapping.functions is not None:
                        #print("Found functions to apply")
                        self.evaluate_functions(field_mapping, lifelog_obj)
                    else:
                        if ll_attribe_type == "datetime":
                            #print("Converting", src_value,"to datetime")
                            try:
                                dt_attr_value=self.cal.parseDT(src_value)[0].isoformat()
                            except:
                                #TODO: Fix Silent return, find a way to identify corrupt row
                                return
                            lifelog_obj.__setattr__(ll_attrib_name,dt_attr_value)
                        # Count type will be mapped to a dict as target[src] -> Not sure if needed
                        # elif ll_attribe_type == "count":
                        #     count_dict = lifelog_obj.__getattribute__(field_mapping.target)
                        #     if src_value not in count_dict.keys():
                        #         count_dict[src_value]=1
                        #     else:
                        #         count_dict[src_value]+= 1
                        else:
                            # Simple mapping
                            lifelog_obj.__setattr__(ll_attrib_name, src_value)
                    #print(ll_attrib_name,"=",lifelog_obj.__getattribute__(ll_attrib_name))
                else:
                    raise Exception("Failed to map", field_mapping.src,". Not present in", row)
            elif field_mapping.functions is not None:
                #Case when src field is not present. This is the case for derived fields
                #print("Found functions without source")
                self.evaluate_functions(field_mapping, lifelog_obj)

            else:
                raise Exception("Mapping without either src or function is not supported. "+field_mapping.toJson())
        return lifelog_obj

    def evaluate_functions(self, fieldMapping:FieldMapping, lifelog_obj:LLEntry):
        val=None
        for function in fieldMapping.functions:
            #print("Original func:", function)
            # Update placeholders with actual values
            placeholders = re.findall("\$[A-Za-z_]*", function)
            for placeholder in placeholders:
                ph_value = lifelog_obj.__getattribute__(placeholder.strip("$"))
                #print("For placeholder:", placeholder,"found:",ph_value)
                if ph_value is None:
                    raise Exception("""Trying to replace a value that is not set. Functions should be defined with placeholders
                     already mapped in the LLEntry""", function)
                function = function.replace(placeholder, str(ph_value))

            # A function can either have eval section or exec section, never both
            #print("Final func:", function)
            exec_section = re.match("exec:(.*)", function)
            if exec_section:
                #print("Executing", exec_section.group(1))
                exec(exec_section.group(1).strip())
            eval_section = re.match("eval:(.*)", function)
            if eval_section:
                val = eval(eval_section.group(1).strip())
                #print("Evaluated", eval_section.group(1).strip(), "to", val, type(val))
                lifelog_obj.__setattr__(fieldMapping.target, val)
        return val

#This class supports import of non-nested JSON files
class SimpleJSONImporter(GenericImporter):
    def __init__(self, source_id:int, source_name:str, entry_type:EntryType, configs:SourceConfigs):
        print("JSONImporter")
        super().__init__(source_id, source_name, entry_type, configs)
    
    def import_data(self, field_mappings:list):
        entries = self.get_type_files_deep(str(Path(self.configs.input_directory).absolute()),
                                      self.configs.filename_regex,
                                      self.configs.filetype.split(","))
        if len(entries) == 0:
            print("NotFound: Data expected in", self.configs.input_directory, "while importing for", self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:",self.configs.filetype)
            return
        for entry in tqdm(entries):
            print("Reading File:", entry)
            with open(entry, 'r') as f1:
                r = f1.read()
                user_data = json.loads(r)
            if isinstance(user_data, list):
                for row in tqdm(user_data):
                    obj = self.create_LLEntry(row, field_mappings)
                    data_entry = self.build_db_entry(obj)
                    self.pdc.add_or_replace_personal_data(data_entry,"dedup_key")
            else:
                raise Exception("UserData expected to be a list. Found "+type(user_data))


class CSVImporter(GenericImporter):
    def __init__(self, source_id:int, source_name: str, entry_type: EntryType, configs:SourceConfigs):
        print("CSVImporter")
        super().__init__(source_id, source_name, entry_type, configs)

    def import_data(self, field_mappings: list):
        # Select top level Category -> Maybe
        # Collect info about Data source based on filetype
        # Create a dictionary of inputField to LLEntry field
        # Store into DataSource
        entries = self.get_type_files_deep(str(Path(self.configs.input_directory).absolute()),
                                           self.configs.filename_regex,
                                           self.configs.filetype.split(","))
        if entries is None or len(entries) == 0:
            print("NotFound: Data expected in ", self.configs.input_directory, " while importing for ", self.source_name)
            if self.configs.filename_regex is not None:
                print("File pattern searched for:", self.configs.filename_regex, "extn:",self.configs.filetype)
            return
        for entry in tqdm(entries):
            print("Reading CSV:", entry)
            df = pd.read_csv(entry, skiprows=self.configs.filetype_configs["skiprows"],dtype=str)
            for index, row in tqdm(df.iterrows(), total=df.shape[0]):
                obj = self.create_LLEntry(row.to_dict(), field_mappings)
                if obj is None:
                    # print("Skipping row:", row.to_dict())
                    continue
                data_entry = self.build_db_entry(obj)
                self.pdc.add_or_replace_personal_data(data_entry, "dedup_key")

