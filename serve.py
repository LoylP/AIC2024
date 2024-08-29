from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
# Đảm bảo bạn có hàm get_all_data
from milvus.search_milvus import query, get_all_data
import json

app = FastAPI()
keyframe_path = "\static\HCMAI22_MiniBatch1\Keyframes"
object_detection_path = "\\static\\HCMAI22_MiniBatch1\\Objects"

# Gắn thư mục tĩnh để phục vụ hình ảnh
app.mount("/images", StaticFiles(directory=keyframe_path), name="images")


class SearchQuery(BaseModel):
    search_query: str


def load_object_detection_results(base_path: str):
    detection_results = {}
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            for file_name in os.listdir(folder_path):
                if file_name.endswith(".json"):
                    file_path = os.path.join(folder_path, file_name)
                    try:
                        with open(file_path, 'r') as file:
                            data = json.load(file)
                            detection_results[file_name] = data
                    except (json.JSONDecodeError, IOError) as e:
                        print(f"Error reading {file_path}: {e}")
    return detection_results


detection_results = load_object_detection_results(object_detection_path)


@app.get("/api/search/object")
async def search_objects(search_query: str):
    query = search_query.lower()

    image_base_path = 'static/images/'

    matching_image_paths = []

    for file_name, file_info in detection_results.items():
        folder_name = file_info['folder']
        file_data = file_info['data']

        image_name = os.path.splitext(file_name)[0] + '.jpg'
        image_path = os.path.join(image_base_path, folder_name, image_name)

        class_names = file_data.get('detection_class_names', [])
        class_entities = file_data.get('detection_class_entities', [])
        scores = file_data.get('detection_scores', [])

        for i, entity in enumerate(class_entities):
            if query in entity.lower():
                matching_image_paths.append(
                    os.path.join(folder_name, image_name))
                break

    matching_image_paths = list(set(matching_image_paths))

    if not matching_image_paths:
        raise HTTPException(
            status_code=404, detail="No images found matching the query.")

    return {"images": matching_image_paths}


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Search API!"}


@app.get("/api/milvus/search/")
async def search(search_query: str):
    try:
        results = query(search_query)

        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search(search_query: str):
    app_instance = App()
    results = app_instance.search(search_query, results=25)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    relative_paths = [f"images/{image}" for image in results]
    return JSONResponse(content=relative_paths)

# @app.get("/api/milvus/get_all/")
# async def get_all():
#     try:
#         results = get_all_data()  # Hàm này cần được định nghĩa để lấy toàn bộ dữ liệu từ Milvus

#         return JSONResponse(content=results)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = f"{path_midas}/{filename}"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
