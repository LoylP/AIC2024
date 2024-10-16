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

translator = Translator()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if results:
        for path in results:  
            frame = path.split('/')[-1].split('.')[0] 
            videosID = path.split('/')[-2]
            results_new.append({"path": path, "frame": frame, "videos_ID": videosID})  
            # print(f"Extracted frame number: {frame}") 

    return JSONResponse(content=results_new)

@app.post("/api/search/image")
async def search_image(file: UploadFile = File(...)):
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    results = search_images_by_image(index_model, image_paths, [temp_file_path], k=25)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    results_new = []
    if results:
        for path in results:  
            frame = path.split('/')[-1].split('.')[0]
            videosID = path.split('/')[-2]
            results_new.append({"path": path, "frame": frame, "videos_ID": videosID})  

    os.remove(temp_file_path)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apiAlign:app", host="0.0.0.0", port=8080, reload=True)