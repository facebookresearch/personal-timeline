import pickle
import os
import numpy as np

from typing import List
from sentence_transformers import SentenceTransformer
from src.objects.LLEntry_obj import LLEntrySummary


class QAEngine:
    def __init__(self, path='./'):
        """Create a QA engine for timeline objects
        """
        self.activity_index = pickle.load(open(os.path.join(path, 'activity_index.pkl'), 'rb'))
        self.daily_index = pickle.load(open(os.path.join(path, 'daily_index.pkl'), 'rb'))
        self.trip_index = pickle.load(open(os.path.join(path, 'trip_index.pkl'), 'rb'))

        self.all_summaries = []
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        for summary in self.activity_index.values():
            self.all_summaries.append(summary)
        for summary in self.daily_index.values():
            self.all_summaries.append(summary)
        for summary in self.trip_index.values():
            self.all_summaries.append(summary)
        
        all_sentences = [summary.textDescription for summary in self.all_summaries]
        self.embeddings = self.model.encode(all_sentences) # N * H

    def query(self, text: str, k=9) -> List[LLEntrySummary]:
        """Returns a list of summaries
        """
        query_emb = self.model.encode([text]) # 1 * H
        similarity = np.matmul(self.embeddings, np.transpose(query_emb)) # N * 1

        indices = [(sim[0], idx) for idx, sim in enumerate(similarity)]
        indices.sort(reverse=True)

        result = []
        for _, idx in indices[:k]:
            result.append(self.all_summaries[idx])

        return result
