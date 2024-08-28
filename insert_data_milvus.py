import os
import torch
import open_clip
from PIL import Image
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

image_folder = "static/images"
uri = "https://in01-07c9bfcb4ff890e.aws-ap-southeast-1.vectordb.zillizcloud.com:19531"
token = "db_admin:Uw2?M0(6>)VN1RMb"  # Replace with your actual token

# Connect to Milvus
connections.connect(alias="default", uri=uri, token=token)

# Define the schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64,
                is_primary=True, auto_id=False),
    FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR,
                dim=512)
]
schema = CollectionSchema(fields, description="Image embeddings collection")
collection = Collection("image_embeddings", schema)

device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='openai')
model.to(device)

id_counter = 0
for root, _, files in os.walk(image_folder):
    for file in files:
        if file.endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join(root, file)
            image = Image.open(file_path).convert("RGB")
            image_input = preprocess(image).unsqueeze(0).to(device)

            with torch.no_grad():
                image_embedding = model.encode_image(image_input).cpu().numpy()

            relative_path = os.path.relpath(file_path, image_folder)
            folder_name, image_name = os.path.split(relative_path)

            formatted_path = f"{folder_name}/{image_name}"
            data = [[id_counter], [formatted_path], image_embedding.tolist()]
            collection.insert(data)
            id_counter += 1

index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 100}
}
collection.create_index(field_name="embedding", index_params=index_params)

print("All images have been inserted.")
