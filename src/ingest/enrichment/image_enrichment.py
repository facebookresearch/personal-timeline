import pickle
import os
import torch
import json

from tqdm import tqdm
from src.common.objects.LLEntry_obj import LLEntry
from PIL import Image, ImageOps
from src.ingest.enrichment import socratic
from src.common.persistence.personal_data_db import PersonalDataDBConnector

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
            if os.path.exists(img_path + ".emb"):
                image_features = pickle.load(open(img_path + ".emb", "rb"))
            else:
                if img == None:
                    img = Image.open(img_path)
                image_input = model_dict['clip_preprocess'](img).unsqueeze(0).to(model_dict['device'])
                image_features = model_dict['clip_model'].encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                pickle.dump(image_features, open(img_path + ".emb", "wb"))

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

    def enrich(self, incremental:bool=True):
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
        for row in tqdm(res.fetchall()):
            row_id = int(row[0])
            data:LLEntry = pickle.loads(row[1])
            if data.imageFilePath is not None and \
                len(data.imageFilePath) > 0 and \
                os.path.exists(data.imageFilePath):
                image_tags, _ = ImageEnricher.enhance(data.imageFilePath)
                data.imageCaptions = json.dumps(image_tags)
                self.db.add_or_replace_personal_data({"captions": data.imageCaptions, 
                                                      "captions_done": 1,
                                                      "id": row_id}, "id")
                count += 1

        print("Image Processing completed for ", count, " entries")
