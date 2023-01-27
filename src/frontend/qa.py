import pickle
import os
import numpy as np
import datetime
import pytz
import geopy
import json

from typing import Dict, List, Tuple, Union
from sentence_transformers import SentenceTransformer
from src.common.objects.LLEntry_obj import LLEntrySummary
from src.frontend.summarizer import Summarizer
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import remove_stopwords
from src.common.util import distance, translate_place_name

class QAEngine:
    def __init__(self, summarizer: Summarizer, start_year=2000, end_year=2023):
        """Create a QA engine for timeline objects
        """
        self.activity_index = pickle.load(open('personal-data/app_data/activity_index.pkl', 'rb'))
        self.daily_index = pickle.load(open('personal-data/app_data/daily_index.pkl', 'rb'))
        self.trip_index = pickle.load(open('personal-data/app_data/trip_index.pkl', 'rb'))
        self.summarizer = summarizer

        self.all_summaries = []
        self.all_sentences = []
        self.unique_ids = []
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # home address
        user_info = json.load(open("src/common/user_info.json"))
        # self.home_address = geolocator.geocode(user_info["address"])

        # TODO: move to a global geo engine
        geolocator = geopy.geocoders.Nominatim(user_agent="my_request")
        self.addresses = user_info["addresses"]
        for addr in self.addresses:
            addr["location"] = geolocator.geocode(addr["address"])

        # for summary in self.activity_index.values():
        #     self.all_summaries.append(summary)
        combined = list(self.daily_index.values()) + list(self.trip_index.values())
        self.tag_inverted_index = {}
        self.double_tag_index = {}
        self.double_tag_to_tags = {}
        self.uid_to_summary = {}

        for summary in combined:
            self.all_summaries.append((summary.startTime, summary.endTime))
            self.all_sentences.append(summary.textDescription)
            day = datetime.datetime.fromisoformat(summary.startTime)
            unique_id = '%s_%s_%s_%s' % (summary.type, day.year, day.month, day.day)
            self.uid_to_summary[unique_id] = summary
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
                            self.double_tag_to_tags[double_tag] = (tags[tid1], tags[tid2])
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

    def get_tag_image(self, tag: str, summary: LLEntrySummary) -> List[str]:
        """Return image paths of a tag (an object) in a summary.
        """
        result = []
        try:
            date_str = ', ' + datetime.datetime.fromisoformat(summary.startTime).strftime('%b %d, %Y')
        except:
            date_str = ''
        if summary.objects is not None:
            for key, value in summary.objects.items():
                for v in value:
                    if v['name'] == tag or key == tag:
                        path = v['img_path']
                        path = os.path.join(os.environ["APP_DATA_DIR"],'static', (os.path.split(path)[-1] + '.compressed.jpg'))
                        result.append({"img_path": path, 'name': v['name'] + date_str})
        return result

    def summary_to_tags(self, summary: LLEntrySummary) -> List[str]:
        """Generate the list of tags of a summary.
        """
        tags = set([summary.type])
        if summary.objects is not None:
            for key, value in summary.objects.items():
                tags.add(key)
                for v in value:
                    tags.add(v['name'])
        
        for location in summary.locations:
            if location is not None:
                # is_home = distance((self.home_address.latitude, 
                #                     self.home_address.longitude),
                #                    (location.latitude, location.longitude)) <= 5.0
                # if is_home:
                #     tags.add("home")
                
                lat, lon = location.latitude, location.longitude
                for address in self.addresses:
                    if address["location"] is not None:
                        addr_lat, addr_lon = address["location"].latitude, address["location"].longitude
                        if distance((addr_lat, addr_lon), (lat, lon)) \
                            <= address["radius"]:
                            tags.add(address["name"])
                
                for attr in ["town", "city", "county", "suburb", "state", "country"]:
                    if 'address' in location.raw and attr in location.raw['address']:
                        place_name = location.raw['address'][attr]
                        place_name = translate_place_name(place_name)
                        tags.add(place_name)
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

    def query(self, text: str, k=9) -> List[Union[str, Dict]]:
        """Returns a list of unique_ids or objects of summaries
        """
        # exact year search
        try:
            dt = datetime.datetime.strptime(text, '%Y')
            return ['year_%d' % (dt.year)]
        except:
            pass

        # exact month search
        formats = ['%Y-%m', '%Y/%m', '%m/%Y',
                    '%m-%Y', '%y/%m', '%m/%y']
        for format in formats:
            try:
                dt = datetime.datetime.strptime(text, format)
                return ['month_%d_%d' % (dt.year, dt.month)]
            except:
                pass

        # exact date search
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y',
                    '%y-%m-%d', '%y/%m/%d', '%m/%d/%y']
        for format in formats:
            try:
                dt = datetime.datetime.strptime(text, format)
                return ['day_%d_%d_%d' % (dt.year, dt.month, dt.day)]
            except:
                pass

        # tag search: 1 tag
        for tag in self.tag_inverted_index:
            if text.lower() == tag.lower():
                result = []
                for uid in list(self.tag_inverted_index[tag]):
                    summary = self.uid_to_summary[uid]
                    objects = self.get_tag_image(tag, summary)
                    if len(objects) == 0:
                        result.append(uid)
                    else:
                        obj = objects[0]
                        obj['unique_id'] = uid
                        result.append(obj)
                return result
        
        # tag search: two tag
        text_preprocessed = self.preprocess(text)
        for tag in self.double_tag_index:
            if text_preprocessed.lower() == tag.lower():
                result = []
                for uid in list(self.double_tag_index[tag]):
                    tag1, tag2 = self.double_tag_to_tags[tag]
                    summary = self.uid_to_summary[uid]
                    objects = self.get_tag_image(tag1, summary) + self.get_tag_image(tag2, summary)
                    if len(objects) == 0:
                        result.append(uid)
                    else:
                        obj = objects[0]
                        obj['unique_id'] = uid
                        result.append(obj)
                return result

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
