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
import csv
import pandas as pd


from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredFileLoader
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle
from langchain.docstore.document import Document


def chunk_to_string(ch):
    ch['date'] = ch['date'].map(lambda x:"On " + x + ", ")
    return ' '.join((ch['date'] + ch['desc']).tolist())

def main(argv):
    print(argv[0])
    chunksize = 50
    documents = []
    for chunk in pd.read_csv(argv[0], chunksize=chunksize):
        documents.append(Document(page_content=chunk_to_string(chunk)))

    print(len(documents))

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save vectorstore
    #with open("timeline-vectorstore-faiss-chunk100.pkl", "wb") as f:
    with open("output.pkl", "wb") as f:
        pickle.dump(vectorstore, f)


if __name__ == "__main__":
    main(sys.argv[1:])
