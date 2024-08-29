from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
from milvus.search_milvus import query
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Change this to your frontend URL http://127.0.0.1:8000
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
    results = app_instance.search(search_query, results=100)

    if not isinstance(results, list):
        raise HTTPException(status_code=400, detail="Invalid search results")

    image_data_list = []
    for idx, image_path in enumerate(results):
        frame, file = os.path.split(image_path)
        image_data = ImageData(
            id=idx + 1,
            frame=frame,
            file=file,
            path=image_path
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