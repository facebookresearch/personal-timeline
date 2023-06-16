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
[sys.path.append(i) for i in ['.', '..']]
import csv
import pandas as pd

import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
from src.views_util import *
from configparser import ConfigParser
from datetime import datetime
import json
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle

class Setup:
    def __init__(self, 
                 directory: str):
        self.dir = directory
        print(self.dir)

    def install_metadata(self):

        # read config.ini
        configfile = os.path.join(self.dir, "config.ini")
        print("Reading config file "+configfile)
        config_obj = ConfigParser(comment_prefixes=None)
        config_obj.read(configfile)

        catalogfile = os.path.join(self.dir, "views_metadata.txt")
        print("Reading views catalog file " + catalogfile)
        views_catalog_dict = read_views_catalog(catalogfile)
        views_desc_store = get_desc(views_catalog_dict, short=True)
        tablename_store = get_table_names(views_catalog_dict)

        embedding_model = config_obj['embedding_model']['model']
        # this the encoding for text-embedding-ada-002
        embedding_encoding = config_obj["embedding_model"]["encoding"]
        max_tokens = config_obj["embedding_model"]["max_tokens"] # the maximum for text-embedding-ada-002 is 8191

        views_desc_store = get_desc(views_catalog_dict, short=True)
        df = pd.DataFrame()

        df['tablename'] = tablename_store

        print("Generating embeddings for catalog ... ")
        # read from views metadata file to generate embeddings
        vectors = map(lambda x: get_embedding(x, engine=embedding_model), views_desc_store)
        vectorslist = list(vectors)
        df['embedding'] = vectorslist
        # store embeddings
        embeddingsfile = os.path.join(self.dir, "views_idx.csv")
        df.to_csv(embeddingsfile, index=False)
        print("Stored embeddings to "+embeddingsfile)

    def install_views(self):
        print("Executing command to import views ...")
        createdbfile = os.path.join(self.dir, "create_db.sql")
        cwd = os.getcwd()
        os.chdir(self.dir)
        os.system('```rm -f views_db.sqlite;sqlite3 views_db.sqlite ".read %s"```' % (createdbfile))
        os.chdir(cwd)
        print("Stored views in sqlite db views_db.sqlite")

    def verbalize(self, episodes):
        all_text = []
        all_meta = []
        id2epi = {}
        for i, dt, desc, details in zip(episodes['id'], episodes['date'], episodes['desc'], episodes['details']):
            d = datetime.strptime(dt,"%Y/%m/%d")
            d1 = d.strftime("%m/%d/%Y")
            text = 'On {0}, {1}'.format(d,details)
            metadata = {'source': i}
            all_text.append(text)
            all_meta.append(metadata)
            id2epi[i] = text

        return all_text, all_meta, id2epi

    def install_data_embeddings(self):
        filepath = os.path.join(self.dir, "timeline.json")
        print("Loading "+filepath)
        f = open(filepath)
        data = json.load(f)
        print("Completed")

        #keys = data.keys()
        keys = list(data.keys())
        keys.sort()

        print("Reading timeline data ...")
        dict = { 'id':[], 'date':[], 'desc':[], 'details':[]}
        df = pd.DataFrame(dict)
        for k in keys:
            for episode in data[k]:
                dftem = pd.DataFrame([[k, data[k][episode]['text_template_based']]], columns=['date','desc'])
                df = pd.concat([df, dftem])

        # details column is for Aria data with more detailed description
        df['details'] = df['desc']
        l = []
        for i in range(0,len(df)):
            l.append(i)
        df['id'] = l
            
        print("Generating embedding vectors for timeline data ...")
        textdata, metadata, id2epi = self.verbalize(df)
        embeddings = OpenAIEmbeddings()

        docsearch = FAISS.from_texts(textdata, embeddings, metadatas=metadata)

        # Save vectorstore
        timelineembeddings = os.path.join(self.dir, "timeline.pkl")
        with open(timelineembeddings, "wb") as f:
            pickle.dump(docsearch, f)
        print("Stored embeddings of timeline in " + timelineembeddings)


def main(argv):
    print()
    print("==================================================================")
    print("This script will prepare your datasource for querying by posttext.")
    print("Please make sure you execute the command as follows:")
    print()
    print("python setup.py <directory of your datasource>")
    print()
    print("The directory of your datasource is expected to contain a file views_metadata.txt that describes your views.")
    print("The directory of your datasource is expected to contain a file views_metadata.txt that describes your views and the file config.ini.")
    print()
    print("The directory of your datasource is expected to contain a file create_db.sql that describes how to import your views into sqlite.")
    print()
    print("The directory of your datasource is expected to contain the timeline data file timeline.json that describes the timeline of the person")
    print()
    input("Press any key to continue ...")
    print()

    s = Setup(argv[0])
    print()
    print("Setting up index based on metadata ...")
    s.install_metadata()
    print("Done")
    print()
    print("Setting up views DB ...")
    s.install_views()
    print("Done")
    print()
    print("Setting up embeddings for timeline data ...")
    s.install_data_embeddings()
    print("Done")

    



if __name__ == "__main__":
    main(sys.argv[1:])
