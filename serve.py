from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
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

path_midas = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
app.mount("/images", StaticFiles(directory=path_midas), name="images")

class ImageData(BaseModel):
    id: int
    frame: str
    file: str
    path: str
    similarity: float
    ocr_text: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Search API!"}

@app.get("/api/search")
async def search(
    search_query: str = Query(None, description="Main search query"),
    ocr_filter: str = Query(None, description="Optional OCR filter text"),
    results: int = Query(100, description="Number of results to return")
):
    app_instance = App()
    search_results = app_instance.search(search_query, ocr_filter=ocr_filter, results=results)

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

@app.get("/images/{filename}")
async def serve_image(filename: str):
    file_path = f"{path_midas}/{filename}"
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.post("/api/search_by_image")
async def search_by_image(
    image: UploadFile = File(...),
    ocr_filter: str = Query(None, description="Optional OCR filter text"),
    results: int = Query(100, description="Number of results to return")
):
    app_instance = App()
    
    image_content = await image.read()
    search_results = app_instance.search_by_image(image_content, ocr_filter=ocr_filter, results=results)
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

@app.get("/api/search_similar")
async def search_similar(
    image_path: str = Query(..., description="Path of the image to search similar"),
    ocr_filter: str = Query(None, description="Optional OCR filter text"),
    results: int = Query(100, description="Number of results to return")
):
    app_instance = App()
    
    with open(os.path.join(path_midas, image_path), "rb") as image_file:
        image_content = image_file.read()
    search_results = app_instance.search_by_image(image_content, ocr_filter=ocr_filter, results=results)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
