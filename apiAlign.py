from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from Align import search_images_by_text, index_model, image_paths, search_images_by_image  
import csv
from typing import List
import tempfile
from googletrans import Translator
from fastapi.responses import StreamingResponse
import io
import requests

translator = Translator()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

path = "/home/phuc/Dev/AIC2024/static/keyframes_preprocess"
app.mount("/images", StaticFiles(directory="/home/phuc/Dev/AIC2024/static/keyframes_preprocess"), name="images")

class SearchQuery(BaseModel):
    search_query: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Search API!"}

async def translate_to_english(text):
    try:
        translation = translator.translate(text, dest='en', src='auto')
        return translation.text if translation else text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text
    
@app.get("/api/search")
async def search(search_query: str):
    # Use the Align model to search for images

    translated_query = await translate_to_english(search_query) if search_query else None
    print(f"Original query: {search_query}")
    print(f"Translated query: {translated_query}")


    results = search_images_by_text(index_model, image_paths, [translated_query], k=100)  # Update to use Align model

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    results_new = []
    fps_list = []  
    if results:
        for path in results:  
            frame = path.split('/')[-1].split('.')[0] 
            videosID = path.split('/')[-2]
            # Extract FPS from the CSV file
            with open("static/video_fps.csv", mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['videos_ID'] == videosID:
                        fps = row['FPS']
                        fps_list.append(fps)  
                        break
            fps_float = float(fps)
            time = int(int(frame) * 1000 / fps_float)
            results_new.append({"path": path, "frame": frame, "videos_ID": videosID, "fps": fps, "time": time})  
            # print(f"Extracted frame number: {frame}") 

    return JSONResponse(content=results_new)

@app.post("/api/search/image")
async def search_image(file: UploadFile = File(...)):
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    results = search_images_by_image(index_model, image_paths, [temp_file_path], k=100)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    results_new = []
    fps_list = []
    if results:
        for path in results:  
            frame = path.split('/')[-1].split('.')[0]
            videosID = path.split('/')[-2]
            with open("static/video_fps.csv", mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['videos_ID'] == videosID:
                        fps = row['FPS']
                        fps_list.append(fps)  
                        break
            fps_float = float(fps)
            time = int(int(frame) * 1000 / fps_float)
            results_new.append({"path": path, "frame": frame, "videos_ID": videosID, "fps": fps, "time": time})  

    os.remove(temp_file_path)
    return JSONResponse(content=results_new)

@app.get("/api/search_similar")
async def search_similar(image_path: str = Query(..., description="Path of the image to search similar")):
    image_path = f"static/keyframes_preprocess/{image_path}"  
    
    results = search_images_by_image(index_model, image_paths, [image_path], k=100)
    print("path: ", image_path)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    results_new = []
    fps_list = []  
    if results:
        for path in results:  
            frame = path.split('/')[-1].split('.')[0]
            videosID = path.split('/')[-2]
            with open("static/video_fps.csv", mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['videos_ID'] == videosID:
                        fps = row['FPS']
                        fps_list.append(fps)  
                        break
            fps_float = float(fps)
            time = int(int(frame) * 1000 / fps_float)
            results_new.append({"path": path, "frame": frame, "videos_ID": videosID, "fps": fps, "time": time})  

    return JSONResponse(content=results_new)

@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = f"/home/phuc/Dev/AIC2024/static/keyframes_preprocess/{filename}.jpg"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.post("/api/export-to-csv")
async def export_to_csv(results_new: List[dict]):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', suffix='.csv') as tmpfile:
        writer = csv.writer(tmpfile)
        for result in results_new:
            videos_id = result.get('videos_ID', '')
            frame = result.get('frame', '')
            writer.writerow([videos_id, frame])

    return FileResponse(tmpfile.name, media_type='text/csv', filename='query.csv')

async def serve_images_around(filename: str):
    folder_path = os.path.join(path, os.path.dirname(filename))  
    if not os.path.isdir(folder_path):
        print("Folder not found")
        return None

    all_files = sorted(os.listdir(folder_path))
    
    try:
        index = all_files.index(os.path.basename(filename)) 
    except ValueError:
        print("Image not found")
        return None

    start_index = max(0, index - 7)
    end_index = min(len(all_files), index + 8)  
    surrounding_files = all_files[start_index:end_index]

    # Remove the base path from the image paths
    relative_image_paths = [os.path.relpath(os.path.join(folder_path, img), path) for img in surrounding_files if os.path.isfile(os.path.join(folder_path, img))]
    return relative_image_paths

@app.get("/api/serve-images-around")
async def get_surrounding_images(filename: str = Query(..., description="Path of the image to find surrounding images")):
    images = await serve_images_around(filename)
    if images is None:
        raise HTTPException(status_code=404, detail="Images not found")
    return {"surrounding_images": images}

@app.post("/api/submit-qa")
async def submit_qa(number: int, videos_ID: str, time: float):
    body_data = {
        "answerSets": [
            {
                "answers": [
                    {
                        "text": f"{number}-{videos_ID}-{time}"
                    }
                ]
            }
        ]
    }
    url = "https://eventretrieval.one/api/v2/submit/bec3b699-bdea-4f2c-94ae-61ee065fa76e"
    params = {
        "session": "u3I0UsCTHiOIfBEuYw3d7G34UhKZ16oq"
    }

    try:
        response = requests.post(url, params=params, json=body_data)
        response.raise_for_status() 
        return JSONResponse(content=response.json())
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra: {e}")
    
@app.post("/api/submit-kis")
async def submit_kis(videos_ID: str, start: int, end: int):
    body_data = {
        "answerSets": [
            {
                "answers": [
                    {
                        "mediaItemName": videos_ID,
                        "start": start,
                        "end": end
                    }
                ]   
            }
        ]
    }
    url = "https://eventretrieval.one/api/v2/submit/69ec2262-d829-4ac1-94a2-1aa0a6693266"
    params = {
        "session": "u3I0UsCTHiOIfBEuYw3d7G34UhKZ16oq"
    }

    try:
        response = requests.post(url, params=params, json=body_data)
        response.raise_for_status() 
        return JSONResponse(content=response.json())
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra: {e}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apiAlign:app", host="0.0.0.0", port=8080, reload=True)
