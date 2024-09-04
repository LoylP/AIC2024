from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
from milvus.search_milvus import query
from typing import List, Dict, Optional
from pymongo import MongoClient
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

path_midas = "F:/AI Challenge/AIC2024/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
app.mount("/images", StaticFiles(directory=path_midas), name="images")


class ImageData(BaseModel):
    id: int
    frame: str
    file: str
    path: str


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Search API!"}

# Replace with your DocumentDB connection details
uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['obj-detection']
collection = db['object-detection-results']


@app.get("/api/get-all-objects")
async def get_all_objects():
    # Load unique_classes.json file from static folder
    with open('static/unique_classes.json') as f:
        unique_classes = json.load(f)
    return unique_classes


@app.get("/api/milvus/search")
async def milvus_search(
    search_query: Optional[str] = None,
):
    search_results = query(search_query)
    return JSONResponse(content=search_results)


@app.get("/api/search")
async def search(
    search_query: Optional[str] = None,
    obj_filters: Optional[List[str]] = Query(None),
    obj_position_filters: Optional[str] = None
):
    app_instance = App()
    search_results = app_instance.search(
        search_query, results=100) if search_query else []

    if not isinstance(search_results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    file_paths = [os.path.splitext(image_info['path'])[0] if isinstance(
        image_info, dict) and 'path' in image_info else os.path.splitext(image_info)[0] for image_info in search_results]

    image_data_list = []

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
                        ('ymax' not in position_query or ymax <=
                         position_query.get('ymax', {}).get('$lte', 1))
                    ):
                        filtered_results.append(result)
                        break
    else:
        filtered_results = object_detection_results

    # Build the response list
    for idx, image_info in enumerate(search_results):
        image_path = os.path.splitext(image_info['path'])[0] if isinstance(
            image_info, dict) and 'path' in image_info else os.path.splitext(image_info)[0]

        if any(result['path'] == image_path for result in filtered_results):
            frame, file = os.path.split(image_info['path'])
            image_data = ImageData(
                id=idx + 1,
                frame=frame,
                file=file,
                path=image_info['path']
            )
            image_data_list.append(image_data.dict())

    return JSONResponse(content=image_data_list)


@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = f"{path_midas}/{filename}"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
