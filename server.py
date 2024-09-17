from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
base_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/Video"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/videos/{folder}/{filename}")
async def serve_video(folder: str, filename: str):
    file_path = os.path.join(base_path, folder, filename)  # Construct the full file path
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")  # Debugging line to check the file path
        raise HTTPException(status_code=404, detail="Video not found")
    
    response = FileResponse(file_path)
    response.headers["Accept-Ranges"] = "bytes"  # Thêm header Accept-Ranges
    return response