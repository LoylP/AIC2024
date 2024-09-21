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
from transformers import BeitFeatureExtractor, BeitModel, XLMRobertaTokenizer, XLMRobertaModel, AutoModel

import concurrent.futures

load_dotenv()

uri = os.getenv('MILVUS_URI')
token = os.getenv('MILVUS_TOKEN')

# Connect to Milvus
# connections.connect(alias="default", uri=uri, token=token)
connections.connect(
    alias="default",
    uri=os.getenv('MILVUS_URI'),
    token=os.getenv('MILVUS_TOKEN')
)

# Define the schema for Milvus collection
collection_name = "image_embeddings_h14"
collection = Collection(name=collection_name)

# Replace Elasticsearch client initialization with OpenSearch
region = os.getenv('AWS_REGION')
service = 'aoss'
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
host = os.getenv('HOST_OPENSEARCH')
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Load CLIP
clip_model, _, preprocess = open_clip.create_model_and_transforms(
   'ViT-H/14-quickgelu', pretrained='dfn5b')
clip_model.to(device)

def encode_text(text):
    text_tokens = tokenizer.tokenize(text).to(device)
    with torch.no_grad():
        with autocast():  # Enable mixed precision
            text_features = clip_model.encode_text(text_tokens).float()

    # Convert the tensor to a numpy array and flatten it
    encoded_text = text_features.cpu().numpy().flatten()

    return encoded_text.tolist()


def encode_image(image_content):
    image = Image.open(io.BytesIO(image_content)).convert('RGB')
    image_input = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        with autocast():  # Enable mixed precision
            image_features = clip_model.encode_image(image_input).float()

    # Convert the tensor to a numpy array and flatten it
    encoded_image = image_features.cpu().numpy().flatten()

    return encoded_image.tolist()

# Load BEIT3 model and tokenizer
# beit_model = BeitModel.from_pretrained(
#     'Raghavan/beit3_base_patch16_384_coco_retrieval').to(device)
# feature_extractor = BeitFeatureExtractor.from_pretrained(
#     'Raghavan/beit3_base_patch16_384_coco_retrieval')

# # Load the XLMRoberta tokenizer for BEiT-3
# text_tokenizer = XLMRobertaTokenizer(
#     "/home/loylp/project/AIC2024/static/beit3.spm")

# # Load a text model
# text_model = AutoModel.from_pretrained('bert-base-uncased').to(device)


# def encode_text(text):
#     tokens = text_tokenizer(text, return_tensors="pt", max_length=512,
#                             padding=True, truncation=True).to(device)
#     with torch.no_grad():
#         with autocast():  # Enable mixed precision
#             # Extract the [CLS] token embedding
#             text_features = text_model(
#                 **tokens).last_hidden_state[:, 0, :].float()
#     encoded_text = text_features.cpu().numpy().flatten()
#     return encoded_text.tolist()


# def encode_image(image_content):
#     image = Image.open(io.BytesIO(image_content)).convert('RGB')
#     inputs = feature_extractor(images=image, return_tensors="pt").to(device)
#     with torch.no_grad():
#         with autocast():  # Enable mixed precision
#             # Take the mean of all patches
#             image_features = beit_model(
#                 **inputs).last_hidden_state.mean(dim=1).float()
#     encoded_image = image_features.cpu().numpy().flatten()
#     return encoded_image.tolist()


def frame_to_timestamp(frame, fps):
    return frame / fps  


def calculate_dynamic_threshold(next_queries, combined_results):
    time_differences = []

    for next_query in next_queries:
        # Lấy frame từ next_query và combined_results 
        next_frame_time = frame_to_timestamp(next_query['frame'])
        if next_query['file_path'] in combined_results:
            main_frame_time = frame_to_timestamp(
                combined_results[next_query['file_path']]['frame'])
            time_diff = abs(next_frame_time - main_frame_time)
            time_differences.append(time_diff)

    if time_differences:
        average_time_diff = sum(time_differences) / len(time_differences)
        return average_time_diff * 1.5  # Tăng thêm 50% để tạo độ linh hoạt
    return 10  # Giá trị mặc định nếu không có next_queries


def query(query_text=None, ocr_filter=None, next_queries=None, limit=300, ef_search=200, nprobe=10, fps=25):
    start_time = time.time()
    results = []
    next_results = []  

    # Determine fps based on folder name
    if query_text and 'Videos_L' in query_text and int(query_text.split('Videos_L')[1][0]) >= 13:
        fps = 30

    # Perform Milvus search for the main query if query_text is provided
    if query_text:
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

        for hit in milvus_results:
            for result in hit:
                results.append({
                    "id": result.entity.get("id"),
                    "VideosId": result.entity.get("VideosId").split("/")[-1] if result.entity.get("VideosId") else None,
                    "frame": result.entity.get("frame"),
                    "file_path": result.entity.get("file_path"),
                    "similarity": result.distance,
                    "source": "main"  # Mark as main query result
                })

    # Handle next_queries in parallel
    if next_queries:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_query = {executor.submit(encode_text, next_query): next_query for next_query in next_queries}
            next_results = []
            for future in concurrent.futures.as_completed(future_to_query):
                next_query_embedding = future.result()
                next_query_embedding = torch.tensor(next_query_embedding).to('cpu').numpy()

                next_milvus_results = collection.search(
                    [next_query_embedding],
                    "embedding",
                    search_params,
                    limit=limit,
                    output_fields=["id", "VideosId", "frame", "file_path"]
                )

                for hit in next_milvus_results:
                    for result in hit:
                        next_results.append({
                            "id": result.entity.get("id"),
                            "VideosId": result.entity.get("VideosId").split("/")[-1] if result.entity.get("VideosId") else None,
                            "frame": result.entity.get("frame"),
                            "file_path": result.entity.get("file_path"),
                            "similarity": result.distance,
                            "source": "next"  # Mark as next query result
                        })

    combined_results = {}

    # Add all results from the main query
    for result in results:
        combined_results[result['file_path']] = result

    # Add or update results from the next queries
    for next_result in next_results:
        file_path = next_result['file_path']
        next_frame_time = frame_to_timestamp(next_result['frame'], fps)

        if file_path in combined_results:
            main_frame_time = frame_to_timestamp(combined_results[file_path]['frame'], fps)
            time_difference = abs(next_frame_time - main_frame_time)

            # Update similarity and combined score
            combined_results[file_path]['similarity'] = min(
                combined_results[file_path]['similarity'], next_result['similarity'])
            combined_results[file_path]['combined_score'] = combined_results[file_path].get('combined_score', 1) + 0.5

            # Calculate time difference only if in the same folder
            if combined_results[file_path]['file_path'].split('/')[1] == next_result['file_path'].split('/')[1]:
                threshold_time = calculate_dynamic_threshold(next_queries, combined_results)

                if time_difference < threshold_time:
                    combined_results[file_path]['combined_score'] += 0.2
                else:
                    relevance_factor = 0.8 if next_result['similarity'] < 0.5 else 0.9
                    combined_results[file_path]['combined_score'] *= relevance_factor
                    combined_results[file_path]['similarity'] *= 0.9  # Adjust similarity based on time difference

            combined_results[file_path]['similarity'] *= 0.85

        else:
            combined_results[file_path] = next_result
            combined_results[file_path]['similarity'] *= 0.85  # Decrease weight for new results

    # Apply OCR filtering if provided
    if ocr_filter:
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

            # If the file exists in combined results, update OCR data
            if file_path in combined_results:
                combined_results[file_path]['ocr_text'] = ocr_text
                combined_results[file_path]['ocr_score'] = hit['_score']
            else:
                # If not found, add as a new result
                combined_results[file_path] = {
                    "id": hit['_id'],
                    "VideosId": file_path.split("/")[-2] if file_path else None,
                    "frame": file_path.split("/")[-1] if file_path else None,
                    "file_path": file_path,
                    "ocr_text": ocr_text,
                    "ocr_score": hit['_score'],
                    "similarity": float('inf')  # Set to infinity as we don't have a similarity score
                }

    # Calculate combined score
    for result in combined_results.values():
        query_score = 1 / (1 + result['similarity']) if result['similarity'] != float('inf') else 0
        if 'ocr_score' in result:
            ocr_score = result['ocr_score'] / 10
            result['combined_score'] = (query_score * 0.7 + ocr_score * 0.3)
        else:
            result['combined_score'] = query_score

        if result.get("source") == "next":
            result['combined_score'] += 0.5

    # Sort results by combined score and take top 'limit' results
    final_results = sorted(combined_results.values(), key=lambda x: x.get('combined_score', 0), reverse=True)[:limit]

    return final_results, time.time() - start_time

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
                "folder": hit.entity.get("file_path").split('/')[0]
            }

            # Only fetch OCR text if ocr_filter is provided
            if ocr_filter:
                result_dict["ocr_text"] = get_ocr_text(
                    hit.entity.get("file_path"))

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
        # Check if the response contains hits
        if response.get('hits', {}).get('hits'):
            return response['hits']['hits'][0]['_source']['text']
    except Exception as e:
        print(f"Error retrieving OCR text: {str(e)}")
    return ""


print(f"Device: {device}")
