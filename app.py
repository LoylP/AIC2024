import os
from PIL import Image
import json
import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

class App:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = SentenceTransformer('clip-ViT-B-32')
        self.index = faiss.read_index("static/index.faiss")
        
        with open("static/image_paths.json") as f:
            self.image_paths = json.load(f)

    def search(self, search_text, results=1):
        text_features = self.model.encode([search_text])
        text_features = text_features.astype('float32')
        
        _, indices = self.index.search(text_features, results)
        return [self.image_paths[indices[0][i]] for i in range(results)]

    def run(self):
        while True:
            search_text = input("Search: ")
            if search_text.lower() == "exit":
                break
            try:
                image_path = self.search(search_text)[0]
                image = Image.open(image_path)
                image.show()
            except IndexError:
                print("No results found.")

if __name__ == "__main__":
    app = App()
    app.run()