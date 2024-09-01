import os
from PIL import Image
import json
import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer
from io import BytesIO

class App:
    def __init__(self):
        static_dir = os.path.abspath("static")
        ocr_file = os.path.join(static_dir, "ocr_texts.json")
        
        if not os.path.exists(static_dir):
            raise FileNotFoundError(f"The 'static' directory does not exist: {static_dir}")
        
        if not os.path.exists(ocr_file):
            raise FileNotFoundError(f"The OCR texts file does not exist: {ocr_file}")
        
        with open(ocr_file) as f:
            self.ocr_texts = json.load(f)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = SentenceTransformer('clip-ViT-L-14')
        # Update new index 
        self.index = faiss.read_index("static/index_vit_l_14.faiss")
        
        with open("static/image_paths.json") as f:
            self.image_paths = json.load(f)

    def search(self, search_text, ocr_filter=None, results=100):
        text_features = self.model.encode([search_text])
        text_features = text_features.astype('float32')
        
        D, I = self.index.search(text_features, len(self.image_paths))
        search_results = []
        
        for i in range(len(I[0])):
            idx = int(I[0][i])
            image_path = self.image_paths[idx]
            ocr_text = self.ocr_texts.get(image_path, "")
            
            similarity = float(D[0][i])
            
            if ocr_filter:
                ocr_match_score = self._ocr_match_score(ocr_text, ocr_filter)
                if ocr_match_score > 0:  # Only include results that match OCR filter
                    similarity = similarity * 0.2 + ocr_match_score * 0.8
                else:
                    continue  
            
            result = {
                'path': image_path,
                'similarity': similarity,
                'ocr_text': ocr_text
            }
            search_results.append(result)
        
        search_results.sort(key=lambda x: x['similarity'], reverse=True)
        return search_results[:results]

    def _ocr_match_score(self, ocr_text, ocr_filter):
        ocr_words = set(ocr_text.lower().split())
        filter_words = set(ocr_filter.lower().split())
        matching_words = ocr_words.intersection(filter_words)
        return len(matching_words) / len(filter_words) if filter_words else 0

    def search_by_image(self, image_file, ocr_filter=None, results=100):
        # processing input image
        image = Image.open(BytesIO(image_file))
        image_features = self.model.encode(image)
        image_features = image_features.astype('float32').reshape(1, -1)
        
        # similarity image
        D, I = self.index.search(image_features, len(self.image_paths))
        search_results = []
        
        for i in range(len(I[0])):
            idx = int(I[0][i])
            image_path = self.image_paths[idx]
            ocr_text = self.ocr_texts.get(image_path, "")
            
            similarity = float(D[0][i])
            
            if ocr_filter:
                ocr_match_score = self._ocr_match_score(ocr_text, ocr_filter)
                if ocr_match_score > 0:  # Only include results that match OCR filter
                    similarity = similarity * 0.6 + ocr_match_score * 0.4
                else:
                    continue 
            
            result = {
                'path': image_path,
                'similarity': similarity,
                'ocr_text': ocr_text
            }
            search_results.append(result)
        
        search_results.sort(key=lambda x: x['similarity'], reverse=True)
        return search_results[:results]

    def run(self):
        while True:
            search_text = input("Search query: ")
            if search_text.lower() == "exit":
                break
            ocr_filter = input("OCR filter (optional): ")
            try:
                results = self.search(search_text, ocr_filter=ocr_filter if ocr_filter else None)
                for result in results:
                    print(f"Path: {result['path']}")
                    print(f"Similarity: {result['similarity']:.4f}")
                    print(f"OCR Text: {result['ocr_text'][:100]}...")
                    print()
            except IndexError:
                print("No results found.")

if __name__ == "__main__":
    app = App()
    app.run()