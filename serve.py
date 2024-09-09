from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
import json
from milvus import search_milvus as milvus_search
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from typing import List, Optional
from pymongo import MongoClient
import math
import aiohttp
from googletrans import Translator
import asyncio
import csv
import tempfile

# Add this line
translator = Translator()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

path_midas = "/home/nguyenhoangphuc-22521129/AIC2024/static/keyframes_preprocess"
app.mount("/images", StaticFiles(directory=path_midas), name="images")

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

# MongoDB connection
uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['obj-detection']
collection = db['object-detection-results']

class ImageData(BaseModel):
    id: int
    frame: str
    file: str
    path: str
    similarity: float
    ocr_text: str
    text: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Search API!"}

@app.get("/api/get-all-objects")
async def get_all_objects():
    # Load unique_classes.json file from static folder
    with open('static/unique_classes.json') as f:
        unique_classes = json.load(f)
    return unique_classes

@app.get("/api/milvus/search")
async def search_milvus_endpoint(
    search_query: Optional[str] = Query(None, description="Main search query"),
    ocr_filter: Optional[str] = Query(None, description="Optional OCR filter text"),
    obj_filters: Optional[List[str]] = Query(None),
    obj_position_filters: Optional[str] = None
):
    try:
        # Translate only the search query to English
        if search_query:
            translated_query = await translate_to_english(search_query)
            print(f"Original query: {search_query}")
            print(f"Translated query: {translated_query}")
        else:
            translated_query = None

        # Perform Milvus search with translated query
        milvus_results, search_time = milvus_search.query(translated_query, ocr_filter, limit=1000)  # Increase limit to 1000
        
        # Apply object filters if provided
        if obj_filters or obj_position_filters:
            filtered_results = filter_results_by_objects(milvus_results, obj_filters, obj_position_filters)
        else:
            filtered_results = milvus_results
        
        # Ensure all float values are JSON-compliant
        for result in filtered_results:
            for key, value in result.items():
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        result[key] = None

        # Sort results by combined score (already calculated in search_milvus.py)
        sorted_results = sorted(filtered_results, key=lambda x: x.get('combined_score', 0), reverse=True)[:100]

        return JSONResponse(content={
            "results": sorted_results, 
            "search_time": search_time,
            "original_query": search_query,
            "translated_query": translated_query
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

def filter_results_by_objects(results, obj_filters, obj_position_filters):
    file_paths = [result['file_path'] for result in results]

    mongo_query = {
        "path": {"$in": file_paths}
    }

    # Process object filters if provided
    if obj_filters:
        for obj_filter in obj_filters:
            for key_value in obj_filter.split(','):
                filter_key, filter_value = key_value.split('=')
                filter_value = int(filter_value)
                mongo_query[f"detection_class_entities.{filter_key}"] = filter_value

    # Process position filters if provided
    if obj_position_filters:
        position_query = {}
        for pos_filter in obj_position_filters.split(','):
            filter_key, filter_value = pos_filter.split('=')
            filter_value = float(filter_value)
            if filter_key in ['xmin', 'ymin', 'xmax', 'ymax']:
                position_query[filter_key] = {"$gte": filter_value}

        if position_query:
            mongo_query['detection_boxes'] = {
                "$elemMatch": position_query
            }

    object_detection_results = list(collection.find(mongo_query))

    # Further filter results based on bounding box positions
    filtered_results = []
    if obj_position_filters:
        for result in object_detection_results:
            boxes = result.get('detection_boxes', [])
            if boxes:
                for box in boxes:
                    xmin, ymin, xmax, ymax = map(float, box)
                    if (
                        ('xmin' not in position_query or xmin >= position_query.get('xmin', {}).get('$gte', 0)) and
                        ('ymin' not in position_query or ymin >= position_query.get('ymin', {}).get('$gte', 0)) and
                        ('xmax' not in position_query or xmax <= position_query.get('xmax', {}).get('$lte', 1)) and
                        ('ymax' not in position_query or ymax <= position_query.get('ymax', {}).get('$lte', 1))
                    ):
                        filtered_results.append(result)
                        break
    else:
        filtered_results = object_detection_results

    # Match filtered results with original results
    final_results = [
        result for result in results
        if any(filtered_result['path'] == result['file_path'] for filtered_result in filtered_results)
    ]

    return final_results

@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = f"{path_midas}/{filename}"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.get("/api/search_similar")
async def search_similar(
    image_path: str = Query(...,
                            description="Path of the image to search similar"),
    ocr_filter: str = Query(None, description="Optional OCR filter text"),
    results: int = Query(100, description="Number of results to return")
):
    app_instance = App()

    with open(os.path.join(path_midas, image_path), "rb") as image_file:
        image_content = image_file.read()
    search_results = app_instance.search_by_image(
        image_content, ocr_filter=ocr_filter, results=results)

    if not isinstance(search_results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    image_data_list = []
    for idx, result in enumerate(search_results):
        frame, file = os.path.split(result['path'])
        image_data = ImageData(
            id=idx + 1,
            frame=frame,
            file=file,
            path=result['path'],
            similarity=result['similarity'],
            ocr_text=result['ocr_text']
        )
        image_data_list.append(image_data.dict())

    return JSONResponse(content=image_data_list)

@app.post("/api/milvus/search_by_image")
async def search_milvus_by_image(
    image_url: str = Query(..., description="URL of the image to search"),
    ocr_filter: str = Query(None, description="Optional OCR filter text"),
    results: int = Query(100, description="Number of results to return"),
    obj_filters: Optional[List[str]] = Query(None)
):
    try:
        # Fetch image content from the provided URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                image_content = await response.read()

        search_results, search_time = milvus_search.search_by_image(image_content, ocr_filter=ocr_filter, results=results)
        
        # Apply object filters if provided
        if obj_filters:
            filtered_results = filter_results_by_objects(search_results, obj_filters, None)
        else:
            filtered_results = search_results
        
        # Process the results to ensure JSON compliance
        processed_results = []
        for result in filtered_results:
            processed_result = {}
            for key, value in result.items():
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        processed_result[key] = None
                    else:
                        processed_result[key] = value
                else:
                    processed_result[key] = value
            processed_results.append(processed_result)
        
        return JSONResponse(content={"results": processed_results, "search_time": search_time})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/api/export-to-csv")
async def export_to_csv(results: List[dict]):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', suffix='.csv') as tmpfile:
        writer = csv.writer(tmpfile)
        for result in results:
            videos_id = result.get('VideosId', '')
            frame = result.get('frame', '')
            writer.writerow([videos_id, frame])
    
    return FileResponse(tmpfile.name, media_type='text/csv', filename='query.csv')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def translate_to_english(text):
    try:
        loop = asyncio.get_event_loop()
        translation = await loop.run_in_executor(None, translator.translate, text, 'en', 'auto')
        return translation.text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails
