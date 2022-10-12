import json
import re
from abc import abstractmethod
from pathlib import Path
import os
import pandas as pd

from src.objects.EntryTypes import EntryType
from src.objects.LLEntry_obj import LLEntry
from src.objects.import_configs import SourceConfigs, FieldMapping
import parsedatetime
#Keep imports that may be used in dynamic function evaluation
from datetime import datetime, timedelta

class GenericImporter:
    def __init__(self, source_name:str, entry_type:EntryType):
        print("GenericImporter")
        self.source_name = source_name
        self.entry_type = entry_type
        self.cal = parsedatetime.Calendar()

    @abstractmethod
    def import_data(self, configs:SourceConfigs, field_mappings:list):
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
                        print("Found functions to apply")
                        self.evaluate_functions(field_mapping, lifelog_obj)
                    else:
                        if ll_attribe_type == "datetime":
                            print("Converting", lifelog_obj.__getattribute__(ll_attrib_name),"to datetime")
                            dt_attr_value=self.cal.parseDT(lifelog_obj.__getattribute__(ll_attrib_name))[0].isoformat()
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
                    print(ll_attrib_name,"=",lifelog_obj.__getattribute__(ll_attrib_name))
                else:
                    raise Exception("Failed to map", field_mapping.src,". Not present in", row)
            elif field_mapping.functions is not None:
                #Case when src field is not present. This is the case for derived fields
                print("Found functions without source")
                self.evaluate_functions(field_mapping, lifelog_obj)

            else:
                raise Exception("Mapping without either src or function is not supported. "+field_mapping.toJson())
        print(lifelog_obj.__dict__)
        return lifelog_obj

    def evaluate_functions(self, fieldMapping:FieldMapping, lifelog_obj:LLEntry):
        val=None
        for function in fieldMapping.functions:
            print("Original func:", function)
            # Update placeholders with actual values
            placeholders = re.findall("\$[A-Za-z_]*", function)
            for placeholder in placeholders:
                ph_value = lifelog_obj.__getattribute__(placeholder.strip("$"))
                print("For placeholder:", placeholder,"found:",ph_value)
                if ph_value is None:
                    raise Exception("""Trying to replace a value that is not set. Functions should be defined with placeholders
                     already mapped in the LLEntry""", function)
                function = function.replace(placeholder, str(ph_value))

            # A function can either have eval section or exec section, never both
            print("Final func:", function)
            exec_section = re.match("exec:(.*)", function)
            if exec_section:
                print("Executing", exec_section.group(1))
                exec(exec_section.group(1).strip())
            eval_section = re.match("eval:(.*)", function)
            if eval_section:
                val = eval(eval_section.group(1).strip())
                print("Evaluated", eval_section.group(1).strip(), "to", val, type(val))
                lifelog_obj.__setattr__(fieldMapping.target, val)
        return val

#This class supports import of non-nested JSON files
class SimpleJSONImporter(GenericImporter):
    def __init__(self, source_name:str, entry_type:EntryType):
        print("JSONImporter")
        super().__init__(source_name, entry_type)
    
    def import_data(self, configs:SourceConfigs, field_mappings:list):
        print("JSON")
        entries = self.get_type_files_deep(str(Path(configs.input_directory).absolute()),
                                      configs.filename_regex,
                                      configs.filetype.split(","))
        if len(entries) == 0:
            print("NotFound: Data expected in ", configs.input_directory, " while importing for ", self.source_name)
            if configs.filename_regex is not None:
                print("File pattern searched for:", configs.filename_regex, "extn:",configs.filetype)
            return
        for entry in entries:
            print("Reading File: ", entry)
            with open(entry, 'r') as f1:
                r = f1.read()
                user_data = json.loads(r)
            if isinstance(user_data, list):
                count=0
                for row in user_data:
                    obj = self.create_LLEntry(row, field_mappings)
                    count+=1
                    if count==10:
                        break


class CSVImporter(GenericImporter):
    def __init__(self, source_name: str, entry_type: EntryType):
        print("CSVImporter")
        super.__init__(source_name, entry_type)

    def import_data(self, configs: SourceConfigs, field_mappings: list):
        # Select top level Category -> Maybe
        # Collect info about Data source based on filetype
        # Create a dictionary of inputField to LLEntry field
        # Store into DataSource
        print("Input dir:", self.input_dir, " is dir? ", os.path.isdir(self.input_dir))
        if os.path.isdir(self.input_dir):
            # Breaking it down to avoid too many files, just in case
            dir_entries = os.listdir(self.input_dir)
            for dir_entry in dir_entries:
                uri = self.input_dir + "/" + dir_entry
                csv_files = self.get_type_files_deep(uri, ["csv"])
                print("CSV files:", csv_files)
                if csv_files is None:
                    continue
                for csv_file in csv_files:
                    print("Reading CSV:", csv_file)
                    # with open(csv_file, newline='') as csvfile:
                    #     reader = csv.DictReader(csvfile)
                    #     for row in reader:
                    #         print(row)
                    df = pd.read_csv(csv_file, skiprows=[2])
                    print("Cols:", df.columns)
                    # for index, row in df.iterrows():
                    #     print(row)


