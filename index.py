import os
from glob import glob
from PIL import Image
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer

# Khởi tạo mô hình
model = SentenceTransformer('clip-ViT-B-32')

# Đường dẫn chính chứa các folder ảnh
image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
chunk_size = 256

embeddings = []
image_files = []

# Duyệt qua tất cả các folder trong đường dẫn
for folder in os.listdir(image_path):
    folder_path = os.path.join(image_path, folder)
    
    # Kiểm tra xem có phải là folder không
    if os.path.isdir(folder_path):
        # Lấy tất cả các file ảnh trong folder
        image_files.extend(glob(os.path.join(folder_path, "*.jpg")))

# Tạo embeddings cho các ảnh
for i in range(0, len(image_files), chunk_size):
    print(f"Processing chunk {i}...")
    chunk = image_files[i:i + chunk_size]
    chunk_embeddings = model.encode([Image.open(image_file) for image_file in chunk])
    embeddings.extend(chunk_embeddings)

# Dựng lên vectorDB với FAISS
dimension = len(embeddings[0])
index = faiss.IndexFlatIP(dimension)
index = faiss.IndexIDMap(index)

vectors = np.array(embeddings).astype('float32')
index.add_with_ids(vectors, np.array(range(len(embeddings))))

# Save index vào file
faiss.write_index(index, "static/index.faiss")

base_dir = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
relative_paths = [os.path.relpath(path, base_dir) for path in image_files]
with open("static/image_paths.json", "w") as f:
    json.dump(relative_paths, f)

print(f"Total images processed: {len(relative_paths)}")