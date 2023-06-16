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



import numpy as np
import pandas as pd
from json import dumps
import re

import sqlite3
from sqlite3 import Error
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function, Where, Parenthesis, TokenList, Comparison, Operation
from sqlparse import tokens as T
from openai.embeddings_utils import get_embedding, cosine_similarity
import dbm
import pickle

# viewspath = ""
# idxpath = ""
# queryfilepath = ""
# views_catalog_dict = {}

def get_embedding_with_cache(text,engine):
    with dbm.open('cache', 'c') as db:
        if text in db:
            return pickle.loads(db[text])
        else:
            res = get_embedding(text,engine=engine)
            db[text] = pickle.dumps(res)
            return res

# define user defined function fuzzy LIKE based on comparing embeddings
def _customLIKE(arg1,arg2):
    # code for arg1 LIKE arg2
    #arg1 is the source string, arg2 is the target string

    embedding_model = "text-embedding-ada-002"
    #embedding_model = "text-similarity-davinci-001"
    a1 = arg1.strip()
    a2 = arg2.strip()
    if a1 == a2:
        return 1.0
    elif a1 == "" or a2 == "":
        return 0.0
    else:
        v1 = get_embedding_with_cache(a1,engine=embedding_model)
        v2 = get_embedding_with_cache(a2,engine=embedding_model)
        maxres = cosine_similarity(v1,v2)
        
        """
        v1 = get_embedding_with_cache(a1,engine=embedding_model)
        a1len = len(a1.split(" ")) + 2
        a2list = a2.split(" ")
        maxres = 0
        substr = ""
        for i in range(0,len(a2list)):
            if i+a1len > len(a2list):
                substr = ' '.join(a2list[i:len(a2list)])
            else:
                substr = ' '.join(a2list[i:i+a1len])
                i = i + a1len
                
            v2 = get_embedding_with_cache(substr,engine=embedding_model)
            res = cosine_similarity(v1,v2)
            if maxres < res:
                maxres = res
            if i+a1len > len(a2list):
                break
        """
        print(maxres)
        # long target strings tend to "dilute" the scores
        if len(arg2) > 8*len(arg1):
            threshold = 0.84
        elif len(arg2) > 4*len(arg1):
            threshold = 0.86
        else:
            threshold = 0.88

        if maxres > threshold:
            return 1 #true
        else:
            return 0 #false


def raise_missing_field_error(error_str):
    format_dict = {"field_name":error_str}
    output_str = "Missing {field_name} field."
    print(output_str.format(**format_dict))
    sys.exit(2)

# read metadata about views and create index
def read_views_catalog(viewspath):

    views_dict = {}

    i = 0
    with open(viewspath, "r") as f:
        while True:
            table_desc = {}
            nm = ""
            description = ""
            schema = ""
            additional_context = ""
            foreign_key = ""
            attr_desc = []
            line = f.readline()
            if not line: 
                break
            # skip lines with "##" at the beginning
            while line.startswith("##"):
                line = f.readline()
                if not line:
                    break

            if line.startswith("name:"):
                i = line.index("name:")
                nm = line[i+len("name:"):].strip()

                line = f.readline()
                if not line:
                    raise_missing_field_error("description")
                if "description:" in line:
                    i = line.index("description:")
                    description = line[i+len("description:"):].strip()
                    table_desc["description"] = description

                line = f.readline()
                if not line:
                    raise_missing_field_error("schema")
                if "schema:" in line:
                    i = line.index("schema:")
                    schema = line[i+len("schema:"):].strip()
                    table_desc["schema"] = schema

                line = f.readline()
                if not line:
                    raise_missing_field_error("example queries:")
                if "example queries:" in line:
                    i = line.index("example queries:")
                    schema = line[i+len("example queries:"):].strip()
                    table_desc["example queries"] = schema

                line = f.readline()
                if not line:
                    raise_missing_field_error("additional_context")
                if "additional_context" in line:
                    i = line.index("additional_context:")
                    additional_context = line[i+len("additional_context:"):].strip()
                    if len(additional_context) == 0:
                        table_desc["additional_context"] = ""
                    else:
                        table_desc["additional_context"] = additional_context

                line = f.readline()
                if not line:
                    raise_missing_field_error("foreign key")
                if "foreign key:" in line:
                    i = line.index("foreign key:")
                    foreign_key = line[i+len("foreign key:"):].strip()
                    table_desc["foreign_key"] = foreign_key
                
                attribute_desc = []
                schema = {}
                while True:
                    line = f.readline()
                    if len(line.strip()) == 0:
                        break
                    attribute_desc.append(line.strip())
                    # store schema of table
                    j = line.find(":")
                    attrname = line[0:j].strip()
                    k = line.find("//")
                    attrtype = line[j+1:k].strip()
                    schema[attrname] = attrtype
                     
                table_desc["attrs"] = attribute_desc
                table_desc["schema"] = schema

            if len(nm)>0:
                views_dict[nm] = table_desc

    f.close()
    return views_dict


# assumes sql query is of the form
#SELECT column1, column2,....,columnN
#FROM tableName
#WHERE [conditions]
#GROUP BY column1
#HAVING [conditons]
#ORDER BY column2
#LIMIT

def escapeSingleQuote(str):
    newstr = ''
    for i in range(0,len(str)):
        if str[i] == "'":
            newstr = newstr + "''"
        else: 
            newstr = newstr + str[i]
    return newstr

def strip_percent(str):
    # remove beginning and end % from string. '%%video games%%' --> 'video games'
    i = 0
    print(str)
    while (str[i]=='%'):
        i = i + 1  
    j = len(str) - 1
    while (str[j]=='%'):
        j = j - 1          
    return str[i:j+1]  
 

def prep_SQL(sql, question, schema):
    sql = sqlparse.format(sql, strip_comments=True).strip()
    p = sqlparse.parse(sql)[0]

    newsql = ""
    question = escapeSingleQuote(question)
    for t0 in p.tokens:
        if t0.value.upper() == 'HAVING':
            newsql = newsql + "HAVING"
        elif isinstance(t0, Where):
            # deep dive into Where clause
            tokeniter = iter(t0.tokens)
            while True:
                try:
                    t1 = next(tokeniter)
                except StopIteration:
                    break
                if isinstance(t1,Comparison):
                    t1list = t1.tokens
                    k = 0
                    while not (t1list[k].ttype==T.Comparison):
                        k = k + 1
                    comp_op = t1list[k]
                    attrname = t1.left.value
                    value = t1.right.value
                    if (isinstance(t1.right,Parenthesis)):
                        newsql = newsql + attrname + " " + comp_op.value + " " + prep_SQL(value, question, schema)
                    elif comp_op.value in ["=", "<", ">", "<=", ">=", "!=", "IN"]:
                        if attrname in schema.keys() and schema[attrname] == "TEXT" and comp_op.value == "=" and (t1.right.ttype == T.Literal.String.Single):
                            # of the form attrname = 'strvalue'
                            #TODO: avoid hardcoding 0.85
                            value = escapeSingleQuote(value[1:len(value)-1])
                            #newsql = newsql + "(" + attrname + " LIKE '%" + value + "%' OR CLOSE('"+question + " " + attrname + ":" + value + "'," + attrname + ")>0.88)"
                            newsql = newsql + "(" + attrname + " LIKE '%" + value + "%' OR CLOSE('" + strip_percent(value) + "', " + attrname + "))"
                        else:
                            newsql = newsql + t1.value
                    elif comp_op.value == 'LIKE':
                        if (t1.right.ttype == T.Literal.String.Single):
                            value = escapeSingleQuote(value[1:len(value)-1])
                            compstr = t1.left.value + " LIKE '" + value +"'"
                            #newsql = newsql + "(" + compstr + " OR CLOSE('"+ question + " " + attrname + ":" + value + "'," + attrname+")>0.88)"
                            newsql = newsql + "(" + attrname + " LIKE '%" + value + "%' OR CLOSE('" + strip_percent(value) + "', " + attrname + "))"
                        else:
                            newsql = newsql + t1.value
                elif isinstance(t1,Parenthesis):
                    # check if next element is a DML
                    # recurse on this sub condition or subquery
                    newsql = newsql + prep_SQL(t1.value, question, schema)
                elif (t1.ttype==None): #likely a substatement, recurse
                    newsql = newsql + prep_SQL(t1.value, question, schema)
                elif not(t1.value.strip() == "#"):
                    newsql = newsql + t1.value
        elif (t0.value[0] == "(" and (isinstance(t0,Parenthesis) or t0.ttype==None)):
            #a substatement, recurse without "(...)"
            sub = t0.value
            remainingstr = ""
            if sub[len(sub)-1] == ')':
                sub = sub[1:len(sub)-1]
            else:
                # find last ')'
                ridx = sub.rfind(')')
                remainingstr = sub[ridx+1:]
                sub = sub[1:ridx]
            newsql = newsql + "(" + prep_SQL(sub, question, schema) + ")" + remainingstr
        elif not (t0.value.strip() == "#"):
            # keep existing tokens
            newsql = newsql + t0.value

    return newsql



# return description of views as a list
def get_desc(views_catalog_dict, short):
    desc = []
    for key in views_catalog_dict:
        table_desc = views_catalog_dict[key]
        if short:
            table_desc_short = {}
            table_desc_short['description'] = table_desc['description']
            table_desc_short['example queries'] = table_desc['example queries']
            table_desc_short['additional_context'] = table_desc['additional_context']
            desc.append(dumps(table_desc_short))
        else:
            desc.append(dumps(table_desc))
    return desc


def get_table_names(views_catalog_dict):
    names = []
    for key in views_catalog_dict:
        names.append(key)
    return names
