import os
import torch
import open_clip
import json
from PIL import Image
import numpy as np
from pymilvus import connections, Collection
import time
from open_clip import tokenizer
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
    'ViT-H/14-quickgelu', pretrained='dfn5b')
clip_model.to(device)


def encode_text(text):
    # Tokenize and encode text
    text_tokens = tokenizer.tokenize(text)
    with torch.no_grad():
        text_features = clip_model.encode_text(text_tokens).float()

    # Convert the tensor to a numpy array and flatten it
    encoded_text = text_features.cpu().numpy().flatten()

    return encoded_text.tolist()


def query(query_text):
    # Encode the query text
    query_embedding = encode_text(query_text)
    print(f"Query embedding shape: {len(query_embedding)}")  # Debugging line

    # Define search parameters with HNSW index
    search_params = {
        "metric_type": "L2",
        "params": {
            "ef": 200  # ef parameter for HNSW
        }
    }

    # Perform the search
    search_results = collection.search(
        [query_embedding],
        "embedding",
        search_params,
        limit=100,
        output_fields=["VideosId", "frame", "file_path"]
    )
    # store the search results
    results = [
        {
            "VideosId": hit.entity.get('VideosId'),
            "frame": hit.entity.get('frame'),
            "file_path": hit.entity.get('file_path')
        }
        for result in search_results for hit in result
    ]
    return results


def get_all_data():
    try:
        # Retrieve all data from Milvus
        all_entities = collection.query(expr=None, output_fields=[
                                        "id", "embedding", "VideosId", "frame", "file_path"])

        # Directly return results
        return [
            {
                "id": entity.get("id"),
                "embedding": entity.get("embedding"),
                "VideosId": entity.get("VideosId"),
                "frame": entity.get("frame"),
                "file_path": entity.get("file_path")
            }
            for entity in all_entities
        ]
    except Exception as e:
        print(f"Error retrieving data from Milvus: {str(e)}")
        return []
