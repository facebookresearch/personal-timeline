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

#from .retrieval_qa import RetrievalBasedQA
#from .views_qa import ViewBasedQA
from .views_qa import *
from .retrieval_qa import *
from typing import Dict
from configparser import ConfigParser


class PostText:

    def __init__(self, 
                 config: Dict,
                 directory: str):
        """Original code parameters.
        """
        # self.retrieval_qa = RetrievalBasedQA(config, directory)
        self.view_qa = ViewBasedQA(config, directory)


    def query(self, question: str):
        """Process the query using all available QA components.
        """
        print("Computing with views:")
        formattedprompt = ""
        sqlquery_before = ""
        sqlquery = ""
        view_res = ""
        eng_answer = ""
        provenance_ids = ""
        retrieval_res = ""

        view_error = False
        rag_error = False

        try:
            formattedprompt, sqlquery_before, sqlquery, view_res, eng_answer, provenance_ids = self.view_qa(question)
            print("View-based answer:")
            print(view_res)
            print(eng_answer)
            print("Sources:", end="")
            print(provenance_ids)
        except Exception as error:
            view_res = error
            eng_answer = error
            print('Unsuccessful with view-based computation, please use only RAG answer. [', error, ']')
            view_error = True

        # try:
        #     print("RAG answer:")
        #     retrieval_res = self.retrieval_qa(question)
        #     print(retrieval_res)
        # except Exception as error:
        #     print('Unsuccessful with RAG-based computation: [', error, ']')
        #     retrieval_res = ""
        #     rag_error = True

        if view_error and rag_error:
            raise Exception("Error in computing answer")
        else:
            return formattedprompt, sqlquery_before, sqlquery, view_res, eng_answer, provenance_ids, retrieval_res

def main(argv):
    #Read config.ini file
    if len(argv[0]) <= 0:
        print("posttext.py <path to dataset directory>")
        return

    config = ConfigParser(comment_prefixes=None)
    directory = argv[0]
    config.read(os.path.join(directory, "config.ini"))

    # create a posttext instance
    posttext = PostText(config, directory)

    # process a single query
    while True:
        print()
        print()
        print("PostText v0.0 ====>")
        question = input("Enter your question:\n")
        if len(question.strip())==0:
            continue
        try:
            posttext.query(question)
        except Exception as error:
            print("No success in computing an answer: [", error, "]")
            print("Please try again. Ctrl-C to end.")


if __name__ == "__main__":
    main(sys.argv[1:])
