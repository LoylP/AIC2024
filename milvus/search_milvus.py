import os
import torch
import open_clip
import json
from PIL import Image
import numpy as np
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
import time
from dotenv import load_dotenv
load_dotenv()

uri = os.getenv('MILVUS_URI')
token = os.getenv('MILVUS_TOKEN')

# Connect to Milvus
connections.connect(alias="default", uri=uri, token=token)

# Define the schema for Milvus collection
collection_name = "image_embeddings"
collection = Collection(name=collection_name)

# Load CLIP and SentenceTransformer models
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai')
clip_model.to(device)
text_model = SentenceTransformer('clip-ViT-B-32')


def encode_text(text):
    return text_model.encode(text).astype('float32').tolist()


def query(query_text):
    # Measure the start time
    start_time = time.time()
    query_embedding = encode_text(query_text)
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}
    }
    search_results = collection.search(
        [query_embedding],
        "embedding",
        search_params,
        limit=10,
        output_fields=["file_path"]
    )
    results = [hit.entity.get('file_path')
               for result in search_results for hit in result]

    end_time = time.time()
    query_time = end_time - start_time

    return {
        "query_time": query_time,
        "results": results
    }

def get_all_data():
    try:
        # Lấy tất cả dữ liệu từ Milvus
        all_entities = collection.query(expr=None, output_fields=["file_path"])
        results = [entity["file_path"] for entity in all_entities]
        return results
    except Exception as e:
        print(f"Error retrieving data from Milvus: {str(e)}")
        return []