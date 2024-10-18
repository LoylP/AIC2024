import os
from glob import glob
from PIL import Image
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer
# Thay đổi mô hình thành ViT-L/14
model = SentenceTransformer('clip-ViT-L-14')

image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
chunk_size = 32
# max_images = 50  # Set the maximum number of images to process

embeddings = []
image_files = []

for folder in os.listdir(image_path):
    folder_path = os.path.join(image_path, folder)
    if os.path.isdir(folder_path):
        image_files.extend(glob(os.path.join(folder_path, "*.jpg")))
        # if len(image_files) >= max_images:            ### chạy với số lượng ảnh nhất định
        #     image_files = image_files[:max_images]    ###  
        #     break                                     ###

# Generate embeddings for images
for i in range(0, len(image_files), chunk_size):
    print(f"Processing chunk {i}/{len(image_files)}...")
    chunk = image_files[i:i + chunk_size]
    
    chunk_embeddings = model.encode([Image.open(image_file) for image_file in chunk])
    embeddings.extend(chunk_embeddings)

# Create vectorDB with FAISS
dimension = len(embeddings[0])  # ViT-L/14
index = faiss.IndexFlatIP(dimension)
index = faiss.IndexIDMap(index)

vectors = np.array(embeddings).astype('float32')
index.add_with_ids(vectors, np.array(range(len(embeddings))))

# Save index to file
# faiss.write_index(index, os.path.abspath("static/index.faiss"))  ## Nếu thành công thì xóa
faiss.write_index(index, os.path.abspath("static/index_vit_l_14.faiss"))

base_dir = os.path.abspath("/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes")
relative_paths = [os.path.relpath(path, base_dir) for path in image_files]

# Save image paths
with open(os.path.abspath("static/image_paths.json"), "w") as f:
    json.dump(relative_paths, f)

print(f"Total images processed: {len(relative_paths)}")
