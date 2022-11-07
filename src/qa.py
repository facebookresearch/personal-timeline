import pickle
import os
import numpy as np
import datetime
import pytz
import geopy.distance
import geopy
import json

from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
from src.objects.LLEntry_obj import LLEntrySummary
from src.summarizer import Summarizer
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import remove_stopwords


class QAEngine:
    def __init__(self, summarizer: Summarizer, path='./', start_year=2000, end_year=2023):
        """Create a QA engine for timeline objects
        """
        self.activity_index = pickle.load(open(os.path.join(path, 'activity_index.pkl'), 'rb'))
        self.daily_index = pickle.load(open(os.path.join(path, 'daily_index.pkl'), 'rb'))
        self.trip_index = pickle.load(open(os.path.join(path, 'trip_index.pkl'), 'rb'))
        self.summarizer = summarizer

        self.all_summaries = []
        self.all_sentences = []
        self.unique_ids = []
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # home address
        geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
        user_info = json.load(open("user_info.json"))
        self.home_address = geolocator.geocode(user_info["address"])

        # for summary in self.activity_index.values():
        #     self.all_summaries.append(summary)
        combined = list(self.daily_index.values()) + list(self.trip_index.values())
        self.tag_inverted_index = {}
        self.double_tag_index = {}

        for summary in combined:
            self.all_summaries.append((summary.startTime, summary.endTime))
            self.all_sentences.append(summary.textDescription)
            day = datetime.datetime.fromisoformat(summary.startTime)
            unique_id = '%s_%s_%s_%s' % (summary.type, day.year, day.month, day.day)
            self.unique_ids.append(unique_id)
    
            # inverted index
            tags = self.summary_to_tags(summary)
            for tag in tags:
                if tag not in self.tag_inverted_index:
                    self.tag_inverted_index[tag] = set([])
                self.tag_inverted_index[tag].add(unique_id)

            # create index for 2 tags
            for tid1 in range(len(tags)):
                for tid2 in range(len(tags)):
                    if tid1 != tid2:
                        double_tag = tags[tid1] + ' ' + tags[tid2]
                        double_tag = self.preprocess(double_tag)
                        if double_tag not in self.double_tag_index:
                            self.double_tag_index[double_tag] = set([])
                        self.double_tag_index[double_tag].add(unique_id)

        indexed = set(self.unique_ids)
        # make days and trips searchable
        start_date = datetime.datetime(start_year, 1, 1)
        end_date = datetime.datetime(end_year, 1, 1)
        
        day = start_date
        while day <= end_date:
            next_day = day + datetime.timedelta(days=1)

            unique_id = 'day_%s_%s_%s' % (day.year, day.month, day.day)
            if unique_id not in indexed:
                summary = self.summarizer.summarize((day.isoformat(), 
                                             next_day.isoformat()), brief=True)
                text = self.summary_to_text(summary)
                if text.strip() != "":
                    self.all_summaries.append((day.date().isoformat(), 
                                            next_day.date().isoformat()))
                    
                    # text = unique_id + ' ' + text
                    self.all_sentences.append(text)
                    self.unique_ids.append(unique_id)
            
            day = next_day
        
        self.embeddings = self.model.encode(self.all_sentences) # N * H

    def summary_to_tags(self, summary: LLEntrySummary) -> List[str]:
        """Generate the list of tags of a summary.
        """
        tags = set([])
        if summary.objects is not None:
            for key, value in summary.objects.items():
                tags.add(key)
                for v in value:
                    tags.add(v['name'])
        
        for location in summary.locations:
            if location is not None:
                is_home = geopy.distance.geodesic((self.home_address.latitude, 
                                                   self.home_address.longitude),
                                        (location.latitude, location.longitude)).km <= 5.0
                if is_home:
                    tags.add("home")
                
                for attr in ["town", "city", "county", "suburb", "state", "country"]:
                    if 'address' in location.raw and attr in location.raw['address']:
                        tags.add(location.raw['address'][attr])
        return list(tags)

    def summary_to_text(self, summary: Dict) -> str:
        """Convert a summarizer output to text.
        """
        text = ""
        for value in summary.values():
            if 'text' in value and value['text'] != "":
                text += value['text'] + ' '
        return text

    def convert(self, date_str_list: List[str]):
        """Convert a list of datetime string to datetime
        """
        res = []
        for date_str in date_str_list:
            if date_str == '':
                date_str = date_str_list[0]
            try:
                dt = datetime.datetime.fromisoformat(date_str).replace(tzinfo=pytz.utc)
            except:
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
            res.append(dt.date())

        return tuple(res)

    def subsetof(self, suma: Tuple[str], sumb: Tuple[str]):
        """Return true if summary a summary a is a subset of summary b
        """
        ra = self.convert(list(suma))
        rb = self.convert(list(sumb))
        return rb[0] <= ra[0] <= rb[1] and rb[0] <= ra[1] <= rb[1]

    def preprocess(self, text: str):
        """lower-case, tokenize and remove stopwords.
        """
        text = remove_stopwords(text.lower())
        tokens = simple_preprocess(text)
        return ' '.join(tokens)

    def query(self, text: str, k=9) -> List[str]:
        """Returns a list of unique_ids of summaries
        """
        # exact date search
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y',
                    '%y-%m-%d', '%y/%m/%d', '%m/%d/%y']
        for format in formats:
            try:
                dt = datetime.datetime.strptime(text, format)
                return ['day_%d_%d_%d' % (dt.year, dt.month, dt.day)]
            except:
                pass
        
        # tag search
        for tag in self.tag_inverted_index:
            if text.lower() == tag.lower():
                return list(self.tag_inverted_index[tag])
        
        # two tag
        text_preprocessed = self.preprocess(text)
        for tag in self.double_tag_index:
            if text_preprocessed.lower() == tag.lower():
                return list(self.double_tag_index[tag])

        # similarity search
        query_emb = self.model.encode([text]) # 1 * H
        similarity = np.matmul(self.embeddings, np.transpose(query_emb)) # N * 1

        indices = [(sim[0], idx) for idx, sim in enumerate(similarity)]
        indices.sort(reverse=True)

        result = []

        for _, idx in indices:
            time_range = self.all_summaries[idx]
            unique_id = self.unique_ids[idx]
            overlap = False

            # diversifying the result
            for i in range(len(result)):
                summ, _ = result[i]
                if self.subsetof(summ, time_range):
                    result[i] = (time_range, unique_id)
                    overlap = True
                    break
                elif self.subsetof(time_range, summ):
                    overlap = True
                    break

            if not overlap:
                result.append((time_range, unique_id))
                if len(result) >= k:
                    break
        
        # return a list of unique ids
        result = [item[1] for item in result]
        return result
