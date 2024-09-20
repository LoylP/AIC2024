import os
import torch
from PIL import Image
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from tqdm import tqdm  # Import tqdm for progress bar
from transformers import BeitImageProcessor, BeitModel

# Configuration
image_folder = "./keyframes_preprocess/"
uri = 'https://in01-5ce0d1eea2a0135.gcp-asia-southeast1.vectordb.zillizcloud.com:443'
token = "db_admin:Tp9!Nx;Cnar7ONy7"  # Replace with your actual token

# Connect to Milvus
connections.connect(alias="default", uri=uri, token=token)

# Define the schema for Milvus collection
fields = [
    FieldSchema(name="id", dtype=DataType.INT64,
                is_primary=True, auto_id=False),
    FieldSchema(name="VideosId", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="frame", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=500),
    # Adjusted to match BEiT3 output dimension
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
]
schema = CollectionSchema(fields, description="Image embeddings collection")
collection = Collection("image_embeddings_beit3_coco_base", schema)

# Load BEiT3 model for CPU usage
model = BeitModel.from_pretrained('Raghavan/beit3_base_patch16_384_coco_retrieval')
model.eval()  # Set the model to evaluation mode
image_processor = BeitImageProcessor.from_pretrained('Raghavan/beit3_base_patch16_384_coco_retrieval')

# Count total images for progress tracking
total_images = sum([len(files) for _, _, files in os.walk(image_folder)])

# Initialize the progress bar
with tqdm(total=total_images, desc="Processing images", unit="image") as pbar:
    id_counter = 0
    for root, _, files in os.walk(image_folder):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png")):
                file_path = os.path.join(root, file)
                image = Image.open(file_path).convert("RGB")

                # Preprocess the image
                image_input = image_processor(images=image, return_tensors="pt")

                with torch.no_grad():
                    outputs = model(**image_input)
                    # Extract [CLS] token embedding
                    image_embedding = outputs.last_hidden_state[:, 0, :].numpy()

                # Extract folder name and image name
                relative_path = os.path.relpath(file_path, image_folder)
                folder_name, image_name = os.path.split(relative_path)
                frame_name = os.path.splitext(image_name)[0]

                # Create a path in the desired format
                formatted_path = f"{folder_name}/{image_name}"

                # Insert data into Milvus
                data = [[id_counter], [folder_name], [frame_name],
                        [formatted_path], image_embedding.tolist()]
                collection.insert(data)
                id_counter += 1

                # Update the progress bar
                pbar.update(1)

# Create an index for fast searching using HNSW
index_params = {
    "index_type": "HNSW",
    "metric_type": "L2",
    "params": {"M": 256, "efConstruction": 1024}
}

collection.create_index(field_name="embedding", index_params=index_params)

print("All images have been processed, inserted, and indexed with HNSW for maximum accuracy.")

