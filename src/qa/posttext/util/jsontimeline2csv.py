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
import sys
import pandas as pd
from collections import OrderedDict

def main(argv):
    filepath = argv[0]
    print("Loading "+filepath)
    f = open(filepath)
    data = json.load(f)
    print("Completed")

    #keys = data.keys()
    keys = list(data.keys())
    keys.sort()

    print("Converting to csv .", end="")
    dict = { 'id':[], 'date':[], 'desc':[], 'details':[]}
    df = pd.DataFrame(dict)
    for k in keys:
        for episode in data[k]:
            dftem = pd.DataFrame([[k, data[k][episode]['text_template_based']]], columns=['date','desc'])
            df = pd.concat([df, dftem])
            print(".", end="")

    # details column is for Aria data with more detailed description
    df['details'] = df['desc']
    l = []
    for i in range(0,len(df)):
        l.append(i)
    df['id'] = l

    print("")
    df.to_csv(argv[1], index=False)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
