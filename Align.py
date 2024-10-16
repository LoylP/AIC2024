import os
from glob import glob
from PIL import Image
import numpy as np
import faiss
import torch
from transformers import AlignProcessor, AlignModel
import random
import json

processor = AlignProcessor.from_pretrained("kakaobrain/align-base")
model = AlignModel.from_pretrained("kakaobrain/align-base")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

def encode_text(query_texts):
    text_features = []
    for query in query_texts:
        inputs = processor(text=query, return_tensors="pt")
        inputs = inputs.to(device)
        with torch.no_grad():
            outputs = model.get_text_features(**inputs)
        text_features.append(outputs.cpu().numpy().flatten())
    return np.array(text_features)

def search_images_by_text(index, image_paths, query_texts, k=100):
    query_features = encode_text(query_texts)
    distances, indices = index.search(query_features, k)
    results = []
    for i, idx_list in enumerate(indices):
        # print(f"Top {k} similar images for query: {query_texts[i]}")
        for idx in idx_list:
            image_path = image_paths[idx]
            results.append(image_path)
            # print(f"Image: {image_path}")
    return results

def encode_image(image_paths):
    image_features = []
    for image_path in image_paths:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        inputs = inputs.to(device)
        with torch.no_grad():
            outputs = model.get_image_features(**inputs)
        image_features.append(outputs.cpu().numpy().flatten())
    return np.array(image_features)

def search_images_by_image(index, image_paths, query_images, k=100):
    query_features = encode_image(query_images)
    distances, indices = index.search(query_features, k)
    results = []
    for i, idx_list in enumerate(indices):
        for idx in idx_list:
            image_path = image_paths[idx]
            results.append(image_path)
    return results

index_model = faiss.read_index("static/AlignModel_index.faiss")
with open("static/AlignPaths.json") as f:
    image_paths = json.load(f)

# query_texts = ["a sunset over the mountains"]
# results = search_images_by_text(index_model, image_paths, query_texts)
image_path = "static/keyframes_preprocess/Videos_L04/L04_V003/1504.jpg"
results = search_images_by_image(index_model, image_paths, [image_path])
print(results)