# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
from pathlib import Path
import json
import os
from src.common.objects.import_configs import DataSourceList

bootstrap_file = "src/common/bootstrap/data_source.json"
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
            os.makedirs(dir_for_reading_input, exist_ok=True)
        else:
            print(dir_for_reading_input, "already exists!")