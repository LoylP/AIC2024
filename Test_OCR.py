import os
import re
import cv2
import numpy as np
import easyocr

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(denoised)
    return contrast

def perform_ocr(image_path):
    processed_img = preprocess_image(image_path)
    reader = easyocr.Reader(['vi', 'en'], gpu=True)  # Sử dụng mô hình tiếng Việt và GPU
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

# Example usage
if __name__ == "__main__":
    image_path = "/home/nguyenhoangphuc-22521129/AIC2024/static/HCMAI22_MiniBatch1/Keyframes/C02_V0001/041760.jpg"
    
    ocr_results = perform_ocr(image_path)
    filtered_text = process_ocr_result(ocr_results)

    print("\nFiltered Vietnamese Text:", filtered_text)