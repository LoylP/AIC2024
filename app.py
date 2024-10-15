from faiss import read_index
from PIL import Image
import numpy as np

import json
import torch
from transformers import AlignProcessor, AlignModel


class App:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Thay thế mô hình clip bằng AlignModel
        self.processor = AlignProcessor.from_pretrained("kakaobrain/align-base")
        self.model = AlignModel.from_pretrained("kakaobrain/align-base").to(self.device)
        self.model.eval()

        self.index = read_index("static/AlignModel_index.faiss")
        with open("static/AlignPaths.json") as f:
            self.image_paths = json.load(f)

    def encode_text(self, query_texts):  # Thêm phương thức encode_text
        text_features = []
        for query in query_texts:
            inputs = self.processor(text=query, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
            text_features.append(outputs.cpu().numpy().flatten())
        return np.array(text_features)

    def search(self, search_text, results=1):
        query_texts = [search_text] 
        text_features = self.encode_text(query_texts)  

        _, indices = self.index.search(text_features, results)
        return [self.image_paths[indices[0][i]] for i in range(results)]

    def run(self):
        while True:
            search_text = input("Search: ")
            if search_text == "exit":
                break
            image_path = self.search(search_text)[0]
            image = Image.open(image_path)
            image.show()


if __name__ == "__main__":
    app = App()
    app.run()
