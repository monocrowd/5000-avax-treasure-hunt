from os import path
import requests
import pandas as pd
import json
import glob
import cv2
import os
from collections import defaultdict
import time

total_supply = 10000 # max total supply, the download will stop at last mint

# Download metadata json and images
os.makedirs("metadata", exist_ok=True)
os.makedirs("images", exist_ok=True)
for id in range(0, total_supply):        
    json_file = f"metadata/{id}.json"

    pat = f"images/{id}-*.png"    
    if len(glob.glob(pat)) > 0:
        continue
    
    print(json_file)
    metadata = None
    if path.exists(json_file):
        with open(json_file, 'rb') as f:
            metadata = json.load(f)
    else:
        url = f"https://51.158.105.175:80/{id}.json"
        r = requests.get(url, verify="51-158-105-175-chain.pem")
        if r.status_code == 200:
            metadata = json.loads(r.content)
            if 'error' in metadata:
                print(f"Token {id} not minted yet")
                break
            with open(json_file, 'wb') as f:
                f.write(r.content)
        else:
            print(f"failed to get metadata for id: {id}")
            break

    if metadata:
        image_url = metadata['image']
        x, y, special_ticket = None, None, None
        for attr in metadata['attributes']:
            val = attr['value']
            if attr['trait_type'] == 'X cover coordinate':
                x = val
            elif attr['trait_type'] == 'Y cover coordinate':
                y = val
            else:
                special_ticket = val

        image_file = "images/{id}-{x}_{y}.png"
        print(f"{id} metadata ({x}, {y}): {image_url}")
        r = requests.get(image_url, verify="dweb-link-chain.pem")
        if r.status_code == 200:
            with open(f"images/{id}-{x}_{y}.png", 'wb') as f:
                f.write(r.content)
        else:
            print(f"failed to get image for id: {id}, image_url: {image_url}")

print("all metadata json and images downloaded")

# generate HD cover and download original cover
max_x = 0
max_y = 0
blank_img = cv2.imread('blank.png')

images_dict = defaultdict(lambda: defaultdict(lambda: blank_img))
for p in glob.glob("./images/*.png"):
    x, y = os.path.basename(p).split('.')[0].split('-')[1].split('_')
    x = int(x)
    y = int(y)
    max_x = max(x, max_x)
    max_y = max(y, max_y)
    img = cv2.imread(p)
    images_dict[y][x] = img

images = []
for row in range(max_y):
    r = []
    for col in range(max_x):
        r.append(images_dict[row][col])
    images.append(r)

def concat_tile(im_list_2d):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in im_list_2d])

im_tile = concat_tile(images)
cv2.imwrite('cover_HD.jpg', im_tile)
print("cover_HD generated")

# download cover in website
def current_time():
    return round(time.time() * 1000000)

r = requests.get(f"https://51.158.105.175:8888/cover.png?t={current_time()}", verify="51-158-105-175-chain.pem")
if r.status_code == 200:
    with open('cover.png', 'wb') as f:
        f.write(r.content)

print("original cover downloaded")
