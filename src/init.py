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