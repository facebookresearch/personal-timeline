from pathlib import Path
import json
import os
from src.common.persistence.personal_data_db import PersonalDataDBConnector
from src.common.objects.import_configs import DataSourceList

bootstrap_file = PersonalDataDBConnector().get_data_source_location()
cwd = str(Path().absolute())
bootstrap_file = cwd + "/" + bootstrap_file
with open(bootstrap_file, 'r') as f1:
    r = f1.read()
    json_data = json.loads(r)
    #Create Python Class Object from Json
    ds_list = DataSourceList(json_data)
    for entry in ds_list.data_sources:
        dir_for_reading_input = entry.configs.input_directory
        if not os.path.exists(dir_for_reading_input):
            os.mkdir(dir_for_reading_input)
        else:
            print(dir_for_reading_input, "already exists!")