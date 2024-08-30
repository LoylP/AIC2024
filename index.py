import os
from glob import glob
from PIL import Image
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer
import pytesseract
import cv2

model = SentenceTransformer('clip-ViT-B-32')

image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
chunk_size = 256

embeddings = []
image_files = []
ocr_texts = {}  # Dictionary to store OCR results

def perform_ocr(image_file):
    try:
        # Read image using OpenCV
        img = cv2.imread(image_file)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Apply dilation to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gray = cv2.dilate(gray, kernel, iterations=1)
        
        # Perform OCR on the preprocessed image
        text = pytesseract.image_to_string(gray)
        
        # If no text is found, try again with the original image
        if not text.strip():
            text = pytesseract.image_to_string(Image.open(image_file))
        
        return text.strip()
    except Exception as e:
        print(f"OCR failed for {image_file}: {str(e)}")
        return ""

for folder in os.listdir(image_path):
    folder_path = os.path.join(image_path, folder)
    
    if os.path.isdir(folder_path):
        image_files.extend(glob(os.path.join(folder_path, "*.jpg")))

# Generate embeddings and perform OCR for images
for i in range(0, len(image_files), chunk_size):
    print(f"Processing chunk {i}...")
    chunk = image_files[i:i + chunk_size]
    
    # Generate embeddings
    chunk_embeddings = model.encode([Image.open(image_file) for image_file in chunk])
    embeddings.extend(chunk_embeddings)
    
    # Perform OCR
    for image_file in chunk:
        ocr_text = perform_ocr(image_file)
        ocr_texts[os.path.relpath(image_file, image_path)] = ocr_text

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