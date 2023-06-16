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



import pickle
import os
import langchain

from langchain import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.cache import InMemoryCache
from langchain.chat_models import ChatOpenAI
import datetime

class RetrievalBasedQA:

    def __init__(self, config, directory):
        self.config = config
        self.source_idx_path = os.path.join(directory, config["input"]["source_idx"])
        self.source_vectorstore = self.load_source_vectorstore(self.source_idx_path)
        self.rag_qa_model = config["RAG"]["qa_model"]
        self.rag_temperature = config["RAG"]["temperature"]
        self.rag_topk = config["RAG"]["topk"]
        self.llm = ChatOpenAI(model_name=self.config["RAG"]["qa_model"], temperature=self.config["RAG"]["temperature"])
        
        self.chain = RetrievalQAWithSourcesChain.from_chain_type(self.llm,
                        chain_type="stuff", 
                        reduce_k_below_max_tokens=True,
                        retriever=self.source_vectorstore.as_retriever(search_kwargs={"k": int(self.rag_topk)}))


    def load_source_vectorstore(self, path: str):
        """Load the episode vectorstore from pickle files.
        """
        vectorstore = ""
        with open(path, "rb") as f:
            vectorstore = pickle.load(f)
        return vectorstore

    def query(self, question: str):
        """Use the RetrievalQAWithSourcesChain from langchain for QA.
        """
        e1 = datetime.datetime.now()
        res = self.chain({"question": question})
        e2 = datetime.datetime.now()
        e3 = e2 - e1
        print(f"Elapsed time: {e3}")
        return res

    def __call__(self, question: str):
        return self.query(question)
