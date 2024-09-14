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
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import math
from torch.cuda.amp import autocast  # Import autocast for mixed precision

load_dotenv()

uri = os.getenv('MILVUS_URI')
token = os.getenv('MILVUS_TOKEN')

# Connect to Milvus
# connections.connect(alias="default", uri=uri, token=token)
connections.connect(
    alias="default",
    uri = os.getenv('MILVUS_URI'),
    token=os.getenv('MILVUS_TOKEN')
)

# Define the schema for Milvus collection
collection_name = "image_embeddings_h14"
collection = Collection(name=collection_name)

# Load CLIP and SentenceTransformer models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
clip_model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-H/14-quickgelu', pretrained='dfn5b')
clip_model.to(device)

# Replace Elasticsearch client initialization with OpenSearch
region = 'ap-southeast-1'
service = 'aoss'
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
host = '1292lxh5s7786w68m0ii.ap-southeast-1.aoss.amazonaws.com'

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)

credentials = session.get_credentials().get_frozen_credentials()

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=60,
    max_retries=5,
    retry_on_timeout=True
)

def encode_text(text):
    text_tokens = tokenizer.tokenize(text).to(device)
    with torch.no_grad():
        with autocast():  # Enable mixed precision
            text_features = clip_model.encode_text(text_tokens).float()

    # Convert the tensor to a numpy array and flatten it
    encoded_text = text_features.cpu().numpy().flatten()

    return encoded_text.tolist()


def query(query_text=None, ocr_filter=None, limit=300, ef_search=200, nprobe=10):
    start_time = time.time()
    results = []

    if query_text:
        # Perform Milvus search
        query_embedding = encode_text(query_text)
        query_embedding = torch.tensor(query_embedding).to('cpu').numpy()
        
        search_params = {
            "metric_type": "L2",
            "params": {
                "ef": ef_search,
                "nprobe": nprobe
            }
        }
        
        milvus_results = collection.search(
            [query_embedding],
            "embedding",
            search_params,
            limit=limit,
            output_fields=["id", "VideosId", "frame", "file_path"]
        )
        
        for result in milvus_results:
            for hit in result:
                results.append({
                    "id": hit.entity.get("id"),
                    "VideosId": hit.entity.get("VideosId").split("/")[-1] if hit.entity.get("VideosId") else None,
                    "frame": hit.entity.get("frame"),
                    "file_path": hit.entity.get("file_path"),
                    "similarity": hit.distance,
                })

    if ocr_filter:
        # Perform OpenSearch search for OCR
        es_query = {
            "query": {
                "match": {
                    "text": ocr_filter
                }
            },
            "size": limit  # Use the same limit as Milvus search
        }
        es_results = client.search(index="ocr", body=es_query)
        
        for hit in es_results['hits']['hits']:
            file_path = hit['_source']['path']
            ocr_text = hit['_source']['text']
            
            # Check if this file_path already exists in results
            existing_result = next((item for item in results if item["file_path"] == file_path), None)
            
            if existing_result:
                # If it exists, update the OCR score and text
                existing_result["ocr_score"] = hit['_score']
                existing_result["ocr_text"] = ocr_text
            else:
                # If it doesn't exist, add a new entry
                results.append({
                    "id": hit['_id'],
                    "VideosId": file_path.split("/")[-2] if file_path else None,
                    "frame": file_path.split("/")[-1] if file_path else None,
                    "file_path": file_path,
                    "ocr_text": ocr_text,
                    "ocr_score": hit['_score'],
                    "similarity": float('inf')  # Set to infinity as we don't have a similarity score
                })

    # Calculate combined score
    for result in results:
        if query_text and ocr_filter:
            query_score = 1 / (1 + result['similarity']) if result['similarity'] != float('inf') else 0
            ocr_score = result.get('ocr_score', 0) / 10
            result['combined_score'] = (query_score*0.7 + ocr_score*0.3)
        elif query_text:
            result['combined_score'] = 1 / (1 + result['similarity'])
        elif ocr_filter:
            result['combined_score'] = result.get('ocr_score', 0)
        else:
            result['combined_score'] = 0

    # Ensure all float values are JSON-compliant
    for result in results:
        for key, value in result.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    result[key] = None  # or use a default value like 0

    # Sort by combined score and take top 'limit' results
    results = sorted(results, key=lambda x: x.get('combined_score', 0), reverse=True)[:limit]

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
        with autocast():  # Enable mixed precision
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
            "ef": 100  
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
            
            result_dict = {
                "id": hit.entity.get("id"),
                "VideosId": hit.entity.get("VideosId").split("/")[-1] if hit.entity.get("VideosId") else None,
                "frame": hit.entity.get("frame"),
                "file_path": hit.entity.get("file_path"),
                "similarity": similarity,
            }
            
            # Only fetch OCR text if ocr_filter is provided
            if ocr_filter:
                result_dict["ocr_text"] = get_ocr_text(hit.entity.get("file_path"))
            
            processed_results.append(result_dict)

    # Apply OCR filter if provided
    if ocr_filter:
        processed_results = [
            result for result in processed_results
            if ocr_filter.lower() in result['ocr_text'].lower()
        ]

    return processed_results[:results], time.time() - start_time


def get_ocr_text(file_path):
    if not file_path:
        return ""
    try:
        search_body = {
            "query": {
                "match": {
                    "path": file_path
                }
            }
        }
        response = client.search(
            index="ocr",
            body=search_body
        )
        if response['hits']['hits']:
            return response['hits']['hits'][0]['_source']['text']
    except Exception as e:
        print(f"Error retrieving OCR text: {str(e)}")
    return ""


print(f"Device: {device}")
print(f"CLIP model device: {next(clip_model.parameters()).device}")
