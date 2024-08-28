from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from app import App
from milvus.search_milvus import query, get_all_data  # Đảm bảo bạn có hàm get_all_data
import json

app = FastAPI()
path_midas = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
# Gắn thư mục tĩnh để phục vụ hình ảnh
app.mount("/images", StaticFiles(directory=path_midas), name="images")


class SearchQuery(BaseModel):
    search_query: str


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