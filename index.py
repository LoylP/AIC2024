import os
from glob import glob
from PIL import Image
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer
import cv2
import easyocr
import re

model = SentenceTransformer('clip-ViT-B-32')

image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
chunk_size = 32
# max_images = 50  # Set the maximum number of images to process

embeddings = []
image_files = []
ocr_texts = {}  # Dictionary to store OCR results

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(denoised)
    return contrast

def perform_ocr(image_path):
    processed_img = preprocess_image(image_path)
    reader = easyocr.Reader(['vi', 'en'], gpu=True)
    results = reader.readtext(processed_img)
    return results

vietnamese_pattern = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]')

def is_vietnamese_text(text: str) -> bool:
    vietnamese_words = vietnamese_pattern.findall(text)
    return len(vietnamese_words) >= 2

def clean_text(text: str) -> str:
    return ' '.join(text.split())

def process_ocr_result(ocr_results: list) -> str:
    processed_lines = []
    
    for (bbox, text, prob) in ocr_results:
        cleaned_text = clean_text(text)
        if (len(cleaned_text) > 3 and is_vietnamese_text(cleaned_text)) or (len(cleaned_text) > 2 and prob > 0.7):
            processed_lines.append(cleaned_text)
    
    return ' '.join(processed_lines)

for folder in os.listdir(image_path):
    folder_path = os.path.join(image_path, folder)
    
    if os.path.isdir(folder_path):
        image_files.extend(glob(os.path.join(folder_path, "*.jpg")))
        # if len(image_files) >= max_images:            ### chạy với số lượng ảnh nhất định
        #     image_files = image_files[:max_images]    ###  
        #     break                                     ###

# Generate embeddings and perform OCR for images
for i in range(0, len(image_files), chunk_size):
    print(f"Processing chunk {i}...")
    chunk = image_files[i:i + chunk_size]
    
    # Generate embeddings
    chunk_embeddings = model.encode([Image.open(image_file) for image_file in chunk])
    embeddings.extend(chunk_embeddings)
    
    # Perform OCR
    for image_file in chunk:
        ocr_results = perform_ocr(image_file)
        # print("trước khi xử lý: ", ocr_results)
        filtered_text = process_ocr_result(ocr_results)
        # print("sau khi xử lý: ", filtered_text)
        ocr_texts[os.path.relpath(image_file, image_path)] = filtered_text
        # print("kq: ", ocr_texts)

# Create vectorDB with FAISS
dimension = len(embeddings[0])
index = faiss.IndexFlatIP(dimension)
index = faiss.IndexIDMap(index)

vectors = np.array(embeddings).astype('float32')
index.add_with_ids(vectors, np.array(range(len(embeddings))))

# Save index to file
faiss.write_index(index, os.path.abspath("static/index.faiss"))

base_dir = os.path.abspath("/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes")
relative_paths = [os.path.relpath(path, base_dir) for path in image_files]

# Save image paths
with open(os.path.abspath("static/image_paths.json"), "w") as f:
    json.dump(relative_paths, f)

# Save OCR results
with open(os.path.abspath("static/ocr_texts.json"), "w") as f:
    json.dump(ocr_texts, f)

print(f"Total images processed: {len(relative_paths)}")
print(f"OCR texts extracted: {len(ocr_texts)}")