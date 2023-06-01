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
