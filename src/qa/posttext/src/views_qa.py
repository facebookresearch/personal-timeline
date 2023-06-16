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



import pandas as pd
import openai
import os
import csv
import sqlite3
import datetime
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function, Where, Parenthesis, TokenList, Comparison, Operation

from openai.embeddings_utils import get_embedding, cosine_similarity
from .views_util import *
from .views_util import _customLIKE
from typing import Dict
import pickle

from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)

class ViewBasedQA:

    def __init__(self,
                 config: Dict,
                 directory: str):
        self.config = config
        self.views_path = os.path.join(directory, config["input"]["views_metadata"])
        self.idxpath = os.path.join(directory, config["input"]["views_metadata_idx"])

        self.views_db = os.path.join(directory, config["input"]["views_db"])
        self.model_name = config["Views"]["model_name"]

        self.views_catalog_dict = read_views_catalog(self.views_path)
        self.views_desc_store = get_desc(self.views_catalog_dict, short=True)
        self.tablename_store = get_table_names(self.views_catalog_dict)

        # create embedding dataframe
        self.df = self.load_viewsmetadata_embeddings()

        self.embedding_model = config["embedding_model"]["model"]
        self.sql_prompt = config["sql_prompt"]["prompt"]

        self.in_memory_cache = {} #dictionary for caching results


    def load_viewsmetadata_embeddings(self):
        """Load embeddings from paths.
        """
        df = pd.DataFrame()

        df['tablename'] = self.tablename_store
        if len(self.idxpath) > 0:
            # read from stored embeddings
            df = pd.read_csv(self.idxpath)
            df['embedding'] = df.embedding.apply(eval).apply(np.array)
        else:
            # read from views metadata file to generate embeddings
            vectors = map(lambda x: get_embedding(x, engine=self.embedding_model),
                                                  self.views_desc_store)
            vectorslist = list(vectors)
            df['embedding'] = vectorslist

            # store embeddings
            df.to_csv(self.idxpath, index=False)
        return df

    def match_views(self, question: str):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        xq = get_embedding(question,
                           engine=self.embedding_model)

        self.df['similarity'] = self.df.embedding.apply(lambda x: cosine_similarity(x, xq))
        self.df = self.df.sort_values('similarity', ascending=False, ignore_index=True)
        print(self.df[['tablename','similarity']].to_string())

        tablename = self.df['tablename'][0]
        simscore = self.df['similarity'][0]
        table = self.views_catalog_dict[tablename]
        return tablename, simscore, table

    def generate_provenance_query(self, sqlquery, tablename, key):
        #
        # for each simple SELECT-FROM-WHERE-GROUPBY-HAVING query, generate the provenance 
        #

        sql = sqlparse.format(sqlquery, strip_comments=True).strip()
        p = sqlparse.parse(sql)[0]

        prov_query = "SELECT {} "
        i = sqlquery.find("FROM")
        prov_query = prov_query.format(key) + sqlquery[i:]
        return prov_query
    

    def removeGOH(self, fromclause):
        sql = sqlparse.format(fromclause, strip_comments=True).strip()
        p = sqlparse.parse(sql)[0]

        ptokenlist = p.tokens
        # look for groupby
        i = 0
        while i<len(ptokenlist):
            if ptokenlist[i].ttype == T.Keyword and (ptokenlist[i].value in ['GROUP BY', 'HAVING', 'ORDER BY', 'DESC', 'ASC']):
                ptokenlist.pop(i)      
                #while i<len(ptokenlist) and ptokenlist[i].value not in ['GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']:
                while i<len(ptokenlist) and ptokenlist[i].value not in ['GROUP BY', 'HAVING', 'ORDER BY']:
                    ptokenlist.pop(i)
            else:
                i = i + 1
        returnstr = ''
        i = 0
        while i<len(ptokenlist):
            returnstr = returnstr + ptokenlist[i].value
            i = i + 1
            
        return returnstr


    def generate_prov_query(self, sqlquery, key):
        
        #find SELECT
        sql = sqlparse.format(sqlquery, strip_comments=True).strip()
        p = sqlparse.parse(sql)[0]

        ptokenlist = p.tokens
        prov_query_list = []
        if ptokenlist[0].value == "SELECT":
            prov_query = ""
            fromidx = sqlquery.find("FROM")
            fromclause = sqlquery[fromidx:]
            selectidx = fromclause.find("SELECT")
            if selectidx > 0:
                  prov_query = "SELECT * "
                  prov_query_list.append(prov_query + fromclause)
                  # process subquery
                  fromclause = self.removeGOH(fromclause)
                  prov_query_list = prov_query_list + self.generate_prov_query(fromclause, key)
                  return prov_query_list
            else:
                  # no more subqueries
                  prov_query = "SELECT {} "
                  fromclause = self.removeGOH(fromclause)
                  prov_query_list.append((prov_query + fromclause).format(key))
                  return prov_query_list + self.generate_prov_query(fromclause, key)
        else:
            # dfs for SELECT clause
            for i in range(0, len(ptokenlist)):
                  if ptokenlist[i].ttype == None:
                        # dig in
                        currnode = ptokenlist[i]
                        subquery = currnode.value
                        for j in range(0, len(currnode.tokens)):
                              currtoken = currnode.tokens[j]
                              # recurse on subqueries
                              if isinstance(currtoken,Parenthesis): 
                                    sub = currtoken.value
                                    sub = sub[1:len(sub)-1]
                                    prov_query_list = prov_query_list + self.generate_prov_query(sub, key)
                              elif currtoken.ttype == None:
                                    prov_query_list = prov_query_list + self.generate_prov_query(currtoken.value, key)
            return prov_query_list

    def table_result2English(self, 
                      tablelist,
                      question,
                      result):
        
        prompt_str = """
        Table description: 
        {schema}
        {attrdesc}
        The following is the answer to the question "{question}" based on the table described above. Write an English sentence to describe the answer below.

        {table_result}
        """

        attrdesc = ""
        for table in tablelist:
            for i in table["attrs"]:
                attrdesc = attrdesc + i + "\n\t"
            attrdesc = attrdesc + "\n"
        
        llm = OpenAI(temperature=0.0)
        prompt = PromptTemplate(
            input_variables=["schema", "attrdesc", "question", "table_result"],
            template=prompt_str
        )

        args = {"schema": table["schema"],"attrdesc":attrdesc,"question":question,"table_result":str(result)}
        chain = LLMChain(llm=llm, prompt = prompt)
        return chain.run(args).strip()

    def generate_prompt_example_records(self, 
                                 tablename):
        # retrieve sample rows
        example = ""
        try:
            connection = sqlite3.connect(self.views_db)
            print("Connection to sqlite successful. Running query.")
            sqlquery = "SELECT * FROM "+tablename+" LIMIT 3"
            # run query
            queryresult = pd.read_sql_query(sqlquery, connection)
            if len(queryresult)==0:
                example = "# no examples available"
            else:
                example = queryresult.to_string()
            connection.close()
        except sqlite3.Error as error:
            # TODO: return something
            print("Error while connecting or executing query", error)
            example = ""

        return example

    def query_views(self, 
                    question: str):
        """Process a query.
        """
        if question in self.in_memory_cache.keys():
            print("Loading cached result...")
            view_res = pickle.loads(self.in_memory_cache[question])
            provenance_ids = pickle.loads(self.in_memory_cache[question+'(p-ids)'])
            info_str = "Loaded answer from cache"
            eng_answer = pickle.loads(self.in_memory_cache[question+"(eng)"])
            return info_str, info_str, info_str, view_res, eng_answer, provenance_ids


        # find best matching table
        tablename, simscore, table = self.match_views(question)
        # prepare prompt
        template = self.sql_prompt
        human_message_prompt = HumanMessagePromptTemplate(
                                    prompt=PromptTemplate(
                                    template=template,
                                    input_variables=["tablename","schema","table_desc","example","additional_context","question"],
                                    #input_variables=["question"]
                                    )
                                )
        example = self.generate_prompt_example_records(tablename)

        chat_prompt_template = ChatPromptTemplate.from_messages([human_message_prompt])
        chat = ChatOpenAI(model_name=self.model_name, temperature=0) #uses gpt-3.5-Turbo by default
        chain = LLMChain(llm=chat, prompt=chat_prompt_template)
        dict = {"tablename":tablename,
                "schema":table["schema"],
                "table_desc":table["description"],
                "example":example,
                "additional_context":table["additional_context"],
                "question":question}
        #dict = {"question":question}
        formattedprompt = template.format(**dict)
        response = ""
        try:
            response = chain.run(dict)
        except Exception as error:
            print("Error generating SQL query", error)
            raise Exception("SQL query generation error: " + error)

        # it can happen that the LLM did not find the best matching table appropriate and hence, does not generate an SQL query
        if "SORRY" in response.upper() :
            raise Exception("SQL generation unsuccessful")

        sqlquery = "SELECT " + response
        print(formattedprompt)
        print("Generated SQL code:")
        print(sqlquery)
        sqlquery_before = sqlquery


        sqlquery = prep_SQL(sqlquery, question, table['schema'])
        sqlquery = sqlquery.strip()

        print()
        print("==> Cleaned SQL query:")
        print(sqlquery)

        cursor = None
        connection = None
        queryresult = None
        eng_answer = ""
        try:
            # RUN SQL query
            # connect to sqlite db
            connection = sqlite3.connect(self.views_db)
            cursor = connection.cursor()
            connection.create_function("CLOSE", 2, _customLIKE)
            print("Connection to sqlite successful. Running query.")
            # run query
            cursor.execute(sqlquery)
            queryresult = cursor.fetchall()
            print(queryresult)

            if len(queryresult)==0:
                queryresult = [(None,)]  # so that english translation will make more sense
            
            eng_answer = self.table_result2English([table], question, queryresult)
        except Exception as error:
            print("Unsuccessful at connecting to SQL server or executing query: [", error, ']')
            # halt processing view-based and throw exception
            raise Exception("SQL error: " + error)

        provenance_ids = []
        try:
            #generate query to compute provenance
            #assumption that the key is one attribute
            print()
            print("==> Query for tracking provenance:")
            print("Obtaining table key:")
            getPKquery = "SELECT name FROM pragma_table_info('{}') where pk;"
            getPKquery = getPKquery.format(tablename)
            print(getPKquery)
            cursor.execute(getPKquery)
            key = cursor.fetchall()
            key_str = ""
            for r in key:
                if len(key_str) > 0:
                    key_str = key_str + "," + r[0]
                else:
                    key_str = r[0]

            prov_query_list = self.generate_prov_query(sqlquery, key_str)
            queryid = 0
            for q in prov_query_list:
                print(q)
                cursor.execute(q)
                provenance = cursor.fetchall()
                provenance_ids.append(("q"+str(queryid), q))
                print()
                print('Tuples contributing to query: ')
                for row in provenance:
                    provenance_ids.append(("q"+str(queryid), row))
                queryid = queryid + 1
                print(provenance_ids)
        except Exception as error:
            print("Unsuccessful attempt to generate provenance. Skipping : [", error, ']')
            raise Exception("Provenance SQL error: " + error)


        try:
            cursor.close()
            connection.close()
        except Exception as error:
            print("Unsuccessful at closing SQL server: [", error, "]")

        # store results in cache
        self.in_memory_cache[question] = pickle.dumps(queryresult)
        self.in_memory_cache[question+'(p-ids)'] = pickle.dumps(provenance_ids)
        self.in_memory_cache[question+"(eng)"] = pickle.dumps(eng_answer)

        return formattedprompt, sqlquery_before, sqlquery, queryresult, eng_answer, provenance_ids

    def query(self, question:str):
        e1 = datetime.datetime.now()
        formattedprompt, sqlquery_before, sqlquery, res, eng_answer, provenance_ids = self.query_views(question)
        e2 = datetime.datetime.now()
        e3 = e2 - e1
        print()
        print(f"Elapsed time: {e3}")
        return formattedprompt, sqlquery_before, sqlquery, res, eng_answer, provenance_ids


    def __call__(self, question: str):
        return self.query(question)
