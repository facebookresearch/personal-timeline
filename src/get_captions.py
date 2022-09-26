import json
import sys
import pdb

from PIL import Image
import requests
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
import sys
# from models.blip import blip_decoder
import json
import os

sys.path.append(os.path.relpath("../BLIP/"))
from models import *
from models.blip import blip_decoder

PHOTO_JSONS_FILE = "../data/photo_filenames.json"
IMAGE_SIZE = 384
#OUTPUT_FILE = "photo_captions.json"
OUTPUT_FILE = "temp_photo_captions.json"
output_dir = { }


def get_device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_demo_image(image_path, image_size, device):
    raw_image = Image.open(str(image_path)).convert('RGB')
    w,h = raw_image.size
    
    transform = transforms.Compose([
        transforms.Resize((image_size,image_size),interpolation=InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ]) 
    image = transform(raw_image).unsqueeze(0).to(device)   
    return image


# image_url_list=sys.argv[1]
# pdb.set_trace()
with open(PHOTO_JSONS_FILE, 'r') as f:
  r1 = f.read()
  data = json.loads(r1)
  #image_url_list = data.keys()
  image_url_list = data.values()

print(len(image_url_list))


device=get_device()
model_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_capfilt_large.pth'
model = blip_decoder(pretrained=model_url, image_size=IMAGE_SIZE, vit='base')
model.eval()
model = model.to(device)

count = 0
for image_url in image_url_list:

    count = count +1
    print(count)
    # image_path = "../../photos/" + image_url + ".jpeg"
    image_path = "../photos/" + image_url
    image=load_demo_image(image_path.strip(),IMAGE_SIZE,device)
    with torch.no_grad():
        # beam search
        #caption = model.generate(image, sample=False, num_beams=3, max_length=20, min_length=5) 
        # nucleus sampling
        caption = model.generate(image, sample=True, top_p=0.9, max_length=40, min_length=5)
#        result=json.dumps({'image_id':os.path.basename(image_url.strip()),'captions':caption})
        output_dir[image_url] = caption
        
        

        
result_string=json.dumps(output_dir)
print(result_string)
                      
with open(OUTPUT_FILE, 'w') as f:
  f.write(result_string)




