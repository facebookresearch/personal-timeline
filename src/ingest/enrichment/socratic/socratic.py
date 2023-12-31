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
import torch
import clip
import csv
import wget

url_dict = {'clip_ViTL14_openimage_classifier_weights.pt': 'https://raw.githubusercontent.com/geonm/socratic-models-demo/master/prompts/clip_ViTL14_openimage_classifier_weights.pt',
            'clip_ViTL14_place365_classifier_weights.pt': 'https://raw.githubusercontent.com/geonm/socratic-models-demo/master/prompts/clip_ViTL14_place365_classifier_weights.pt',
            'clip_ViTL14_tencentml_classifier_weights.pt': 'https://raw.githubusercontent.com/geonm/socratic-models-demo/master/prompts/clip_ViTL14_tencentml_classifier_weights.pt'}

checkpoint_path = os.path.join(os.environ["APP_DATA_DIR"],"prompts")
print("Path for storing Socratic Model is ", checkpoint_path)
os.makedirs(checkpoint_path, exist_ok=True)

src_path = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(src_path, 'prompts')

for k, v in url_dict.items():
    file_path = os.path.join(checkpoint_path, k)
    if not os.path.exists(file_path):
        wget.download(v, out=checkpoint_path)

os.environ['CUDA_VISIBLE_DEVICES'] = ''

def load_openimage_classnames(csv_path):
    csv_data = open(csv_path)
    csv_reader = csv.reader(csv_data)
    classnames = {idx: row[-1] for idx, row in enumerate(csv_reader)}
    return classnames


def load_tencentml_classnames(txt_path):
    txt_data = open(txt_path)
    lines = txt_data.readlines()
    classnames = {idx: line.strip() for idx, line in enumerate(lines)}
    return classnames


def build_simple_classifier(clip_model, text_list, template, device):
    with torch.no_grad():
        texts = [template(text) for text in text_list]
        text_inputs = clip.tokenize(texts).to(device)
        text_features = clip_model.encode_text(text_inputs)
        text_features /= text_features.norm(dim=-1, keepdim=True)

    return text_features, {idx: text for idx, text in enumerate(text_list)}


def load_models():
    # build model and tokenizer
    model_dict = {}

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print('\tLoading CLIP ViT-L/14')
    clip_model, clip_preprocess = clip.load("ViT-L/14", device=device)
    print('\tLoading precomputed zeroshot classifier')
    openimage_classifier_weights = torch.load(checkpoint_path + '/clip_ViTL14_openimage_classifier_weights.pt', map_location=device).type(torch.FloatTensor)
    openimage_classnames = load_openimage_classnames(prompt_path + '/openimage-classnames.csv')
    tencentml_classifier_weights = torch.load(checkpoint_path + '/clip_ViTL14_tencentml_classifier_weights.pt', map_location=device).type(torch.FloatTensor)
    tencentml_classnames = load_tencentml_classnames(prompt_path + '/tencent-ml-classnames.txt')
    place365_classifier_weights = torch.load(checkpoint_path + '/clip_ViTL14_place365_classifier_weights.pt', map_location=device).type(torch.FloatTensor)
    place365_classnames = load_tencentml_classnames(prompt_path + '/place365-classnames.txt')

    print('\tBuilding simple zeroshot classifier')
    img_types = ['photo', 'cartoon', 'sketch', 'painting']
    ppl_texts = ['no people', 'people']
    ifppl_texts = ['is one person', 'are two people', 'are three people', 'are several people', 'are many people']
    imgtype_classifier_weights, imgtype_classnames = build_simple_classifier(clip_model, img_types, lambda c: f'This is a {c}.', device)
    ppl_classifier_weights, ppl_classnames = build_simple_classifier(clip_model, ppl_texts, lambda c: f'There are {c} in this photo.', device)
    ifppl_classifier_weights, ifppl_classnames = build_simple_classifier(clip_model, ifppl_texts, lambda c: f'There {c} in this photo.', device)

    tags = 'food,plant,animal,person,vehicle,building,scenery,document,commodity products,other objects'.split(',')
    simple_tag_weights, simple_tag_classnames = build_simple_classifier(clip_model, tags, lambda c: f'This is a photo of {c}.', device)


    model_dict['clip_model'] = clip_model
    model_dict['clip_preprocess'] = clip_preprocess
    model_dict['openimage_classifier_weights'] = openimage_classifier_weights
    model_dict['openimage_classnames'] = openimage_classnames
    model_dict['tencentml_classifier_weights'] = tencentml_classifier_weights
    model_dict['tencentml_classnames'] = tencentml_classnames
    model_dict['place365_classifier_weights'] = place365_classifier_weights
    model_dict['place365_classnames'] = place365_classnames
    model_dict['imgtype_classifier_weights'] = imgtype_classifier_weights
    model_dict['imgtype_classnames'] = imgtype_classnames
    model_dict['ppl_classifier_weights'] = ppl_classifier_weights
    model_dict['ppl_classnames'] = ppl_classnames
    model_dict['ifppl_classifier_weights'] = ifppl_classifier_weights
    model_dict['ifppl_classnames'] = ifppl_classnames
    model_dict['simple_tag_weights'] = simple_tag_weights
    model_dict['simple_tag_classnames'] = simple_tag_classnames
    model_dict['device'] = device

    return model_dict


def drop_gpu(tensor):
    if torch.cuda.is_available():
        return tensor.cpu().numpy()
    else:
        return tensor.numpy()


def zeroshot_classifier(image):
    image_input = model_dict['clip_preprocess'](image).unsqueeze(0).to(model_dict['device'])
    with torch.no_grad():
        image_features = model_dict['clip_model'].encode_image(image_input)
        image_features /= image_features.norm(dim=-1, keepdim=True)

        sim = (100.0 * image_features @ model_dict['openimage_classifier_weights'].T).softmax(dim=-1)
        openimage_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(10)]
        openimage_classes = [model_dict['openimage_classnames'][idx] for idx in indices]

        sim = (100.0 * image_features @ model_dict['tencentml_classifier_weights'].T).softmax(dim=-1)
        tencentml_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(10)]
        tencentml_classes = [model_dict['tencentml_classnames'][idx] for idx in indices]

        sim = (100.0 * image_features @ model_dict['place365_classifier_weights'].T).softmax(dim=-1)
        place365_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(10)]
        place365_classes = [model_dict['place365_classnames'][idx] for idx in indices]

        sim = (100.0 * image_features @ model_dict['imgtype_classifier_weights'].T).softmax(dim=-1)
        imgtype_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(len(model_dict['imgtype_classnames']))]
        imgtype_classes = [model_dict['imgtype_classnames'][idx] for idx in indices]

        sim = (100.0 * image_features @ model_dict['ppl_classifier_weights'].T).softmax(dim=-1)
        ppl_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(len(model_dict['ppl_classnames']))]
        ppl_classes = [model_dict['ppl_classnames'][idx] for idx in indices]

        sim = (100.0 * image_features @ model_dict['ifppl_classifier_weights'].T).softmax(dim=-1)
        ifppl_scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(len(model_dict['ifppl_classnames']))]
        ifppl_classes = [model_dict['ifppl_classnames'][idx] for idx in indices]

    return image_features, openimage_scores, openimage_classes, tencentml_scores, tencentml_classes,\
           place365_scores, place365_classes, imgtype_scores, imgtype_classes,\
           ppl_scores, ppl_classes, ifppl_scores, ifppl_classes


def generate_prompt(openimage_classes, tencentml_classes, place365_classes, imgtype_classes, ppl_classes, ifppl_classes):
    img_type = imgtype_classes[0]
    ppl_result = ppl_classes[0]
    if ppl_result == 'people':
        ppl_result = ifppl_classes[0]
    else:
        ppl_result = 'are %s' % ppl_result

    sorted_places = place365_classes

    object_list = ''
    for cls in tencentml_classes:
        object_list += f'{cls}, '
    for cls in openimage_classes[:2]:
        object_list += f'{cls}, '
    object_list = object_list[:-2]

    prompt_caption = f'''I am an intelligent image captioning bot.
    This image is a {img_type}. There {ppl_result}.
    I think this photo was taken at a {sorted_places[0]}, {sorted_places[1]}, or {sorted_places[2]}.
    I think there might be a {object_list} in this {img_type}.
    A creative short caption I can generate to describe this image is:'''

    return prompt_caption


def sorting_texts(image_features, captions):
    with torch.no_grad():
        text_inputs = clip.tokenize(captions).to(model_dict['device'])
        text_features = model_dict['clip_model'].encode_text(text_inputs)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        sim = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        scores, indices = [drop_gpu(tensor) for tensor in sim[0].topk(len(captions))]
        sorted_captions = [captions[idx] for idx in indices]

    return scores, sorted_captions


def postprocess_results(scores, classes):
    scores = [float('%.4f' % float(val)) for val in scores]
    outputs = []
    for score, cls in zip(scores, classes):
        outputs.append({'score': score, 'output': cls})
    return outputs


global model_dict
model_dict = load_models()

if __name__ == '__main__':
    pass
