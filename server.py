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


@app.get("/api/search")
async def search(
    search_query: str,
    obj_filters: Optional[List[str]] = Query(
        None)  # Accept multiple object filters
):
    app_instance = App()
    search_results = app_instance.search(search_query, results=100)

    if not isinstance(search_results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    # Extract file paths from search results and remove '.jpg'
    file_paths = [os.path.splitext(image_info['path'])[0] if isinstance(
        image_info, dict) and 'path' in image_info else os.path.splitext(image_info)[0] for image_info in search_results]

    image_data_list = []

    if obj_filters:
        # Build the MongoDB query for object filters
        mongo_query = {
            "path": {"$in": file_paths}
        }

        # Parse each obj filter (e.g., "Person=3", "Woman=2") and add to the query
        for obj_filter in obj_filters:
            filter_key, filter_value = obj_filter.split('=')
            filter_value = int(filter_value)
            mongo_query[f"detection_class_entities.{filter_key}"] = filter_value

        # Query the MongoDB collection for matching object detection data
        object_detection_results = list(collection.find(mongo_query))

        # Filter search results based on object filters
        for idx, image_info in enumerate(search_results):
            image_path = os.path.splitext(image_info['path'])[0] if isinstance(
                image_info, dict) and 'path' in image_info else os.path.splitext(image_info)[0]

            # Check if image_path matches any file_path in object_detection_results
            if any(result['path'] == image_path for result in object_detection_results):
                frame, file = os.path.split(image_info['path'])
                image_data = ImageData(
                    id=idx + 1,
                    frame=frame,
                    file=file,
                    path=image_info['path']
                )
                image_data_list.append(image_data.dict())

    else:
        # No object filter, return all search results
        for idx, image_info in enumerate(search_results):
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
