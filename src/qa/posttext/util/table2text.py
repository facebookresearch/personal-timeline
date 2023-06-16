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



import os
import sys
import pandas as pd


def verbalize(episodes, template):
    all_text = []
    numcols = len(episodes.columns)
    for idx, row in episodes.iterrows():
        s = template.format(**row)
        all_text.append(s)

    return all_text

def main(argv):

    episodes = pd.read_csv(argv[0])
    template = argv[1]

    textdata = verbalize(episodes, template)

    text_file = open(argv[0]+".txt", "w")
    for s in textdata:
        text_file.write(s)
        text_file.write("\n")
    text_file.close()


if __name__ == "__main__":
    main(sys.argv[1:])
