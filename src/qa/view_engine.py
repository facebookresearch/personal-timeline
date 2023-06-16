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
import langchain
from langchain.llms import OpenAI
from langchain import PromptTemplate


from configparser import ConfigParser
from langchain.cache import InMemoryCache
from posttext.src.posttext import PostText
langchain.llm_cache = InMemoryCache()


class ViewEngine:

    def __init__(self, path):
        print(path)
        config = ConfigParser(comment_prefixes=None)
        config.read(os.path.join(path, 'config.ini'))
        self.posttext = PostText(config, path)
        self.llm = OpenAI()

    def verbalize(self, query: str, answer: str):
        template = "Question: {query}\n\nAnswer: {context}\n\n Can you summarize the answer in a single sentence (durations are in seconds)?"
        prompt = PromptTemplate(
            input_variables=["query", "context"],
            template=template)
        
        return self.llm(prompt.format(query=query, context=answer))


    def flatten(self, lst):
        """Flatten a nested list
        """
        flattened_list = []
        for item in lst:
            if isinstance(item, tuple):
                item = list(item)

            if isinstance(item, list):
                flattened_list.extend(self.flatten(item))
            else:
                flattened_list.append(item)
        return flattened_list

    def query(self, 
              query: str):
        """Answer a query using a View-based QA method.
        """
        formattedprompt, sqlquery_before, sqlquery, view_res, eng_answer, provenance_ids, retrieval_res = self.posttext.query(query)
        
        # print(provenance_ids)
        provenance_ids = self.flatten(provenance_ids)

        # sources = [tpl[1][1] for tpl in sources]
        return {"question": query, 
                "view_res": view_res,
                "eng_answer": eng_answer,
                "answer": eng_answer,
                "sources": provenance_ids,
                "sql": sqlquery,
                "sql_before": sqlquery_before}


if __name__ == '__main__':
    engine = ViewEngine("public/digital_data/")
    print(engine.query("How many cities did I visit when I travel to Japan?"))
