import os
from glob import glob
import cv2
import easyocr
import json
import re

# Initialize the reader once
reader = easyocr.Reader(['vi', 'en'], gpu=True, recog_network='standard')

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(denoised)
    return contrast

def perform_ocr(image_paths):
    processed_imgs = [preprocess_image(path) for path in image_paths]
    results = reader.readtext_batched(processed_imgs)
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
        if (len(cleaned_text) > 3 and is_vietnamese_text(cleaned_text)) or (len(cleaned_text) > 2 and prob > 0.5):
            processed_lines.append(cleaned_text)
    
    return ' '.join(processed_lines)

def process_images_ocr(image_path):
    image_files = []
    ocr_texts = {}
    # max_images = 50  # Chạy thử với 50 ảnh
    for folder in os.listdir(image_path):
        folder_path = os.path.join(image_path, folder)
        if os.path.isdir(folder_path):
            image_files.extend(glob(os.path.join(folder_path, "*.jpg")))
            # if len(image_files) >= max_images:              # Chỉ thử với 50 ảnh
            #     image_files = image_files[:max_images]      #
            #     break                                       #

    batch_size = 10  # Adjust based on your GPU memory
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i+batch_size]
        print(f"Processing OCR for images {i+1}-{min(i+batch_size, len(image_files))}/{len(image_files)}")
        ocr_results = perform_ocr(batch)
        for j, image_file in enumerate(batch):
            filtered_text = process_ocr_result(ocr_results[j])
            print("filtered_text: ", filtered_text)
            ocr_texts[os.path.relpath(image_file, image_path)] = filtered_text

    # Save OCR results
    with open(os.path.abspath("static/ocr_texts.json"), "w") as f:
        json.dump(ocr_texts, f)

    print(f"OCR texts extracted: {len(ocr_texts)}")

if __name__ == "__main__":
    image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes"
    process_images_ocr(image_path)