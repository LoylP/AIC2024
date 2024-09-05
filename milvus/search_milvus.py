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
from sentence_transformers import SentenceTransformer
import io
from elasticsearch import Elasticsearch
import math

load_dotenv()

uri = os.getenv('MILVUS_URI')
token = os.getenv('MILVUS_TOKEN')

# Connect to Milvus
# connections.connect(alias="default", uri=uri, token=token)
connections.connect(
    alias="default",
    uri="https://in01-5ce0d1eea2a0135.gcp-asia-southeast1.vectordb.zillizcloud.com:443",
    token="db_admin:Tp9!Nx;Cnar7ONy7"
)

# Define the schema for Milvus collection
collection_name = "image_embeddings"
collection = Collection(name=collection_name)

# Load CLIP and SentenceTransformer models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
clip_model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-H/14-quickgelu', pretrained='dfn5b')
clip_model.to(device)

# Initialize Elasticsearch client
es = Elasticsearch(["http://localhost:9200"])

def encode_text(text):
    text_tokens = tokenizer.tokenize(text).to(device)
    with torch.no_grad():
        text_features = clip_model.encode_text(text_tokens).float()

    # Convert the tensor to a numpy array and flatten it
    encoded_text = text_features.cpu().numpy().flatten()

    return encoded_text.tolist()


def query(query_text=None, ocr_filter=None):
    start_time = time.time()
    results = []

    if query_text:
        # Perform Milvus search
        query_embedding = encode_text(query_text)
        query_embedding = torch.tensor(query_embedding).to('cpu').numpy()
        
        search_params = {
            "metric_type": "L2",
            "params": {"ef": 200}
        }
        
        limit = 300  # Increase limit to get more potential matches
        
        milvus_results = collection.search(
            [query_embedding],
            "embedding",
            search_params,
            limit=limit,
            output_fields=["id", "VideosId", "frame", "file_path"]
        )
        
        for result in milvus_results:
            for hit in result:
                file_path = hit.entity.get("file_path")
                ocr_text = get_ocr_text(file_path)
                results.append({
                    "id": hit.entity.get("id"),
                    "VideosId": hit.entity.get("VideosId"),
                    "frame": hit.entity.get("frame"),
                    "file_path": file_path,
                    "similarity": hit.distance,
                    "ocr_text": ocr_text
                })

    if ocr_filter:
        # Perform Elasticsearch search for OCR
        es_query = {
            "query": {
                "match": {
                    "text": ocr_filter
                }
            },
            "size": 1000  # Adjust this number as needed
        }
        es_results = es.search(index="ocr_result", body=es_query)
        
        for hit in es_results['hits']['hits']:
            file_path = hit['_source']['path']
            ocr_text = hit['_source']['text']
            
            # Check if this file_path already exists in results
            existing_result = next((item for item in results if item["file_path"] == file_path), None)
            
            if existing_result:
                # If it exists, update the OCR score
                existing_result["ocr_score"] = hit['_score']
            else:
                # If it doesn't exist, add a new entry
                results.append({
                    "file_path": file_path,
                    "ocr_text": ocr_text,
                    "ocr_score": hit['_score'],
                    "similarity": float('inf')  # Set to infinity as we don't have a similarity score
                })

    # Calculate combined score
    for result in results:
        query_score = 1 / (1 + result['similarity']) if result['similarity'] != float('inf') else 0
        ocr_score = result.get('ocr_score', 0)
        
        # Normalize OCR score (assuming max score is 1, adjust if needed)
        normalized_ocr_score = ocr_score / 1 if ocr_score else 0
        
        # Calculate combined score (70% query, 30% OCR)
        combined_score = 0.7 * query_score + 0.3 * normalized_ocr_score
        
        # Handle non-JSON compliant float values
        if math.isnan(combined_score) or math.isinf(combined_score):
            combined_score = 0
        
        result['combined_score'] = combined_score

        # Ensure all float values are JSON-compliant
        for key, value in result.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    result[key] = None  # or use a default value like 0

    # Sort by combined score and take top 100
    results = sorted(results, key=lambda x: x['combined_score'], reverse=True)[:100]

    return results, time.time() - start_time


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


def encode_image(image_content):
    image = Image.open(io.BytesIO(image_content)).convert('RGB')
    image_input = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = clip_model.encode_image(image_input).float()
    
    # Convert the tensor to a numpy array and flatten it
    encoded_image = image_features.cpu().numpy().flatten()
    
    return encoded_image.tolist()


def search_by_image(image_content, ocr_filter=None, results=100):
    # Measure the start time
    start_time = time.time()
    
    # Encode the image
    image_embedding = encode_image(image_content)
    image_embedding = torch.tensor(image_embedding).to('cpu').numpy()
    
    # Define search parameters with HNSW index
    search_params = {
        "metric_type": "L2",
        "params": {
            "ef": 200  # ef parameter for HNSW
        }
    }
    
    # Perform the search
    search_results = collection.search(
        [image_embedding],
        "embedding",
        search_params,
        limit=results,
        output_fields=["id", "VideosId", "frame", "file_path"]
    )
    
    # Process and return results
    processed_results = []
    for result in search_results:
        for hit in result:
            similarity = hit.distance
            # Handle non-JSON compliant float values
            if math.isnan(similarity) or math.isinf(similarity):
                similarity = float('inf')  # or some other appropriate value
            
            processed_results.append({
                "id": hit.entity.get("id"),
                "VideosId": hit.entity.get("VideosId"),
                "frame": hit.entity.get("frame"),
                "file_path": hit.entity.get("file_path"),
                "similarity": similarity,
                "ocr_text": get_ocr_text(hit.entity.get("file_path"))
            })

    # Apply OCR filter if provided
    if ocr_filter:
        processed_results = [
            result for result in processed_results
            if ocr_filter.lower() in result['ocr_text'].lower()
        ]

    return processed_results[:results], time.time() - start_time


def get_ocr_text(file_path):
    try:
        es_query = {
            "query": {
                "match": {
                    "path": file_path
                }
            }
        }
        es_result = es.search(index="ocr_result", body=es_query)
        if es_result['hits']['hits']:
            return es_result['hits']['hits'][0]['_source']['text']
    except Exception as e:
        print(f"Error retrieving OCR text: {str(e)}")
    return ""


print(f"Device: {device}")
print(f"CLIP model device: {next(clip_model.parameters()).device}")
