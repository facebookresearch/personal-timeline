## Example code for running the socratic model

The original repo: [Link](https://huggingface.co/spaces/Geonmo/socratic-models-image-captioning-with-BLOOM)

### Step 1:

Install requirements:
```
pip install -r requirements.txt
```

### Step 2:

Register a Hugging Face account and request a Huggingface access token: [Link](https://huggingface.co/docs/hub/security-tokens)

```
export HF_TOKEN=<the token goes here>
```

### Step 3:

You can run the model by (it will load the model or caption the image in `example.jpg`)

```
python socratic.py
```

Or
```
>>> from socratic import image_captioning
100% [........................................................................] 17133291 / 17133291	Loading CLIP ViT-L/14
	Loading precomputed zeroshot classifier
	Building simple zeroshot classifier
>>> from PIL import Image
>>> img = Image.open('example.jpg')
>>> print(image_captioning(img))
```

The result should be like (running time is about 6-8 seconds per image on CPUs)
```
{'inference_time': {'CLIP inference': 4.495590925216675, 'BLOOM request': 1.8190219402313232}, 'generated_captions': [{'score': 1.0, 'output': '\n    There are two people standing on a street.'}], 'reasoning': {'openimage_results': [{'score': 0.2079, 'output': 'Street sign'}, {'score': 0.0553, 'output': 'Traffic sign'}, {'score': 0.0348, 'output': 'Parking meter'}, {'score': 0.0285, 'output': 'Cable car'}, {'score': 0.0285, 'output': 'Cable car'}, {'score': 0.0229, 'output': 'Taxi'}, {'score': 0.0196, 'output': 'Downtown'}, {'score': 0.0143, 'output': 'Bus stop'}, {'score': 0.014, 'output': 'Mission'}, {'score': 0.0127, 'output': 'Sign'}], 'tencentml_results': [{'score': 0.3026, 'output': 'street sign'}, {'score': 0.0842, 'output': 'cab, hack, taxi, taxicab'}, {'score': 0.0507, 'output': 'parking meter'}, {'score': 0.0307, 'output': 'signboard, sign'}, {'score': 0.0297, 'output': 'cable car, car'}, {'score': 0.0208, 'output': 'bus stop'}, {'score': 0.0185, 'output': 'sign'}, {'score': 0.0176, 'output': 'pole'}, {'score': 0.0157, 'output': 'street'}, {'score': 0.0157, 'output': 'street'}], 'place365_results': [{'score': 0.3173, 'output': 'downtown'}, {'score': 0.1742, 'output': 'street'}, {'score': 0.1349, 'output': 'crosswalk'}, {'score': 0.0962, 'output': 'skyscraper'}, {'score': 0.037, 'output': 'tower'}, {'score': 0.0269, 'output': 'alley'}, {'score': 0.0188, 'output': 'phone booth'}, {'score': 0.0177, 'output': 'parking lot'}, {'score': 0.0148, 'output': 'pagoda'}, {'score': 0.0142, 'output': 'outdoor parking garage'}], 'imgtype_results': [{'score': 0.9236, 'output': 'photo'}, {'score': 0.0515, 'output': 'sketch'}, {'score': 0.021, 'output': 'cartoon'}, {'score': 0.0039, 'output': 'painting'}], 'ppl_results': [{'score': 0.5149, 'output': 'people'}, {'score': 0.4851, 'output': 'no people'}], 'ifppl_results': [{'score': 0.2379, 'output': 'are two people'}, {'score': 0.215, 'output': 'are three people'}, {'score': 0.1875, 'output': 'is one person'}, {'score': 0.1816, 'output': 'are several people'}, {'score': 0.178, 'output': 'are many people'}]}}
```
