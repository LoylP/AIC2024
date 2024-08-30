from fastapi import FastAPI, HTTPException, Query
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
    search_query: str = Query(..., description="Main search query"),
    ocr_filter: str = Query(None, description="Optional OCR filter text")
):
    app_instance = App()
    results = app_instance.search(search_query, ocr_filter=ocr_filter, results=100)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    image_data_list = []
    for idx, result in enumerate(results):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
