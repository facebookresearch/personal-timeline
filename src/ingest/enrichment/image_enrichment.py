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
import torch
import json
import numpy as np

from tqdm import tqdm
from src.common.objects.LLEntry_obj import LLEntry
from PIL import Image, ImageOps
from src.ingest.enrichment import socratic
from src.common.persistence.personal_data_db import PersonalDataDBConnector
from typing import List


class ImageEnricher:
    def __init__(self) -> None:
        self.db = PersonalDataDBConnector()

    def enhance(img_path: str, k=5):
        """Run enhencements.

        Args:
            img_path (str): the path to the images

        Return:
            Dictionary: a dictionary of objects, places, and tags (food, plant, etc.)
            Numpy.ndarray: the CLIP embeddings
        """
        if not os.path.exists(img_path + ".compressed.jpg"):
            # RGBA -> RGB
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.save(img_path + ".compressed.jpg")

        # CLIP embeddings and zero-shot image classification
        model_dict = socratic.model_dict
        drop_gpu = socratic.drop_gpu

        with torch.no_grad():
            if os.path.exists(img_path + ".pt"):
                image_features = torch.load(img_path + ".pt")
            else:
                if img == None:
                    img = Image.open(img_path)
                image_input = model_dict['clip_preprocess'](img).unsqueeze(0).to(model_dict['device'])
                image_features = model_dict['clip_model'].encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                torch.save(image_features, img_path + ".pt")

            sim = (100.0 * image_features @ model_dict['openimage_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            openimage_classes = [model_dict['openimage_classnames'][idx] for idx in indices]

            sim = (100.0 * image_features @ model_dict['tencentml_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            tencentml_classes = [model_dict['tencentml_classnames'][idx] for idx in indices]

            sim = (100.0 * image_features @ model_dict['place365_classifier_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            places = [model_dict['place365_classnames'][idx] for idx in indices]

            objects = openimage_classes + tencentml_classes

            # simple tagging for food, animal, person, vehicle, building, scenery, document, commodity, other objects
            sim = (100.0 * image_features @ model_dict['simple_tag_weights'].T).softmax(dim=-1)
            _, indices = [drop_gpu(tensor) for tensor in sim[0].topk(k)]
            tag = [model_dict['simple_tag_classnames'][idx] for idx in indices][0]
            if tag == 'other objects':
                tags = []
            else:
                tags = [tag]

        embedding = image_features.squeeze(0).cpu().numpy()
        return {"objects": objects, "places": places, "tags": tags}, embedding

    def deduplicate(self, img_paths: List[str]):
        """Deduplicate a list of images.

        Args:
            img_paths (List of str): the image paths

        Returns:
            List of str: the image paths that are duplicate.
        """
        img_paths.sort()
        res = []

        for i in tqdm(range(len(img_paths))):
            img_path = img_paths[i]
            if os.path.exists(img_path + ".emb"):
                image_features = pickle.load(open(img_path + ".emb", "rb"))
                embedding = image_features.squeeze(0).cpu().numpy()

            if i > 0:
                sim = np.dot(embedding, prev_embedding)
                if sim > 0.9:
                    res.append(img_path)
            prev_embedding = embedding
        return res

    def enrich(self, incremental:bool=True):
        # enhencement
        select_cols = "id, data"
        select_count = "count(*)"
        where_clause={"data": "is not NULL"}
        if incremental:
            where_clause["captions_done"] = "=0"
        count_res = self.db.search_personal_data(select_count, where_clause)
        pending = count_res.fetchone()
        if pending is None:
            print("No pending image enrichments")
            return
        # print("Total enrichments to be done: ", pending[0])

        res = self.db.search_personal_data(select_cols, where_clause)
        count = 0
        img_paths = []
        row_ids = []
        for row in tqdm(res.fetchall()):
            row_id = int(row[0])
            row_ids.append(row_id)

            data:LLEntry = pickle.loads(row[1])
            if data.imageFilePath is not None and \
                len(data.imageFilePath) > 0 and \
                os.path.exists(data.imageFilePath):
                image_tags, _ = ImageEnricher.enhance(data.imageFilePath)
                img_paths.append(data.imageFilePath)
                data.imageCaptions = json.dumps(image_tags)
                self.db.add_or_replace_personal_data({"captions": data.imageCaptions,
                                                      "captions_done": 1,
                                                      "id": row_id}, "id")
                count += 1

        # deduplicate
        duplicates = set(self.deduplicate(img_paths))
        print("Found %d duplicates" % len(duplicates))
        for row_id, img_path in zip(row_ids, img_paths):
            self.db.add_or_replace_personal_data({"status": 'duplicate' if img_path in duplicates else 'active',
                                                  "dedup_done": 1,
                                                  "id": row_id}, "id")


        print("Image Processing completed for ", count, " entries")
