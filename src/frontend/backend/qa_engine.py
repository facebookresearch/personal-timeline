import pandas as pd
import pickle
import os
import langchain
from langchain.cache import InMemoryCache
langchain.llm_cache = InMemoryCache()

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import VectorDBQAWithSourcesChain
from langchain import OpenAI
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate

from datetime import datetime

class QAEngine:

    def __init__(self, path, k=10):
        episode_path = os.path.join(path, 'episodes.csv')
        self.episodes = pd.read_csv(episode_path)
        self.id2epi = {}
        textdata, metadata, self.id2epi = self.verbalize(self.episodes)
        embeddings = OpenAIEmbeddings()

        print("Building / loading FAISS index")
        pkl_path = episode_path + '.emb'
        if os.path.exists(pkl_path):
            docsearch = pickle.load(open(pkl_path, 'rb'))
        else:
            print("Number of episodes =", len(textdata))
            docsearch = FAISS.from_texts(textdata, embeddings, metadatas=metadata)
            pickle.dump(docsearch, open(pkl_path, 'wb'))

        template = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
ALWAYS return a "SOURCES" part in your answer.

Example of your response should be:
```
The answer is foo
SOURCES: xyz
```
QUESTION: {question}
=========
{summaries}
=========
FINAL ANSWER:"""
        PROMPT = PromptTemplate(template=template, input_variables=["summaries", "question"])


        self.chain = VectorDBQAWithSourcesChain.from_chain_type(OpenAI(temperature=0),
                                chain_type="stuff",
                                vectorstore=docsearch,
                                chain_type_kwargs={'prompt': PROMPT},
                                k=k)

        # create the view engine
        try:
            view_config_path = os.path.join(path, 'config.ini')
            if os.path.exists(view_config_path):
                from .view_engine import ViewEngine
                self.view_engine = ViewEngine(path)
            else:
                self.view_engine = None
        except:
            self.view_engine = None


    def verbalize(self, episodes: pd.DataFrame):
        """Verbalize the episode table into text.
        """
        all_text = []
        all_meta = []
        id2epi = {}
        for id, dt, desc in zip(episodes['id'], episodes['date'], episodes['desc']):
            text = f'On {datetime.fromisoformat(dt).strftime("%m/%d/%Y")}, {desc}'
            metadata = {'source': id}
            all_text.append(text)
            all_meta.append(metadata)
            id2epi[id] = text

        return all_text, all_meta, id2epi

    def query(self,
              query: str,
              method='Retrieval-based'):
        """Answer a query using a RAG-based QA method over Langchain.
        """
        # query = "Did I run often?"
        print(method)
        print(query)

        if method == 'View-based' and self.view_engine != None:
            res = self.view_engine.query(query)
        else:
            res = self.chain({"question": query})
            res['answer'] = res['answer'].replace('SOURCES:', '')
            res['sources'] = res['sources'].split(', ')

        new_sources = []
        for i in range(len(res['sources'])):
            source = res['sources'][i]
            if source in self.id2epi:
                print(source)
                new_sources.append({'id': source, 'episode': self.id2epi[source]})
                print(self.id2epi[source])

        res['sources'] = new_sources

        return res


if __name__ == '__main__':
    engine = QAEngine('public/digital_data')
    for query in ["Did I run often?", "How many harry potter books did I read?", "Which cities did I visited when I traveled to Japan?"]:
        print(engine.query(query))
