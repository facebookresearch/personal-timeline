import os
import sys
[sys.path.append(i) for i in ['.', '..']]
import csv
import pandas as pd

import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
from src.views_util import *
from configparser import ConfigParser

def main(argv):
    #execute this command in the directory where config.ini is located
    print(argv[0])


    # read config.ini
    config_obj = ConfigParser(comment_prefixes=None)
    config_obj.read(argv[1])

    views_catalog_dict = read_views_catalog(argv[0])
    views_desc_store = get_desc(views_catalog_dict, short=True)
    tablename_store = get_table_names(views_catalog_dict)

    embedding_model = config_obj['embedding_model']['model']
    # this the encoding for text-embedding-ada-002
    embedding_encoding = config_obj["embedding_model"]["encoding"]
    max_tokens = config_obj["embedding_model"]["max_tokens"] # the maximum for text-embedding-ada-002 is 8191

    views_desc_store = get_desc(views_catalog_dict, short=True)
    df = pd.DataFrame()

    df['tablename'] = tablename_store

    # read from views metadata file to generate embeddings
    vectors = map(lambda x: get_embedding(x, engine=embedding_model), views_desc_store)
    vectorslist = list(vectors)
    df['embedding'] = vectorslist
    # store embeddings
    df.to_csv(argv[2], index=False)
    print("stored embeddings to "+argv[2])


if __name__ == "__main__":
    main(sys.argv[1:])
