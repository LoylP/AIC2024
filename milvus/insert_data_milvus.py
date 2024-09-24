import os
import torch
from PIL import Image
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from tqdm import tqdm  # Import tqdm for progress bar
from torch.nn import DataParallel  # For multi-GPU support
from transformers import BeitImageProcessor, BeitModel
from swin_transformer_v2 import SwinTransformerV2  


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

# Check if CUDA is available and detect the number of GPUs
if torch.cuda.is_available():
    device_ids = list(range(torch.cuda.device_count())
                      )  # [0, 1, 2, 3] for 4 GPUs
    print(f"Using {len(device_ids)} GPUs: {device_ids}")
else:
    raise RuntimeError("CUDA is not available. Please check your GPU setup.")

# Load BEiT3 model and wrap it for multi-GPU usage
# model = BeitModel.from_pretrained(
#     'Raghavan/beit3_base_patch16_384_coco_retrieval').cuda()
# model = DataParallel(model, device_ids=device_ids)
# image_processor = BeitImageProcessor.from_pretrained(
#     'Raghavan/beit3_base_patch16_384_coco_retrieval')

# Load Swin model và wrap nó cho việc sử dụng multi-GPU
model = SwinTransformerV2(img_size=384, patch_size=4, in_chans=3, num_classes=0).cuda()  
model = DataParallel(model, device_ids=device_ids)
image_processor = None 

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
                image_input = image.resize((384, 384)) 
                image_input = np.array(image_input).transpose(2, 0, 1)  
                image_input = torch.tensor(image_input).unsqueeze(0).float().to(device_ids[0]) 

                with torch.no_grad():
                    outputs = model(image_input)  
                    image_embedding = outputs.cpu().numpy()  

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
