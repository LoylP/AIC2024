import os
from pymilvus import connections, Collection
from dotenv import load_dotenv


load_dotenv()

uri = os.getenv('MILVUS_URI')
token = os.getenv('MILVUS_TOKEN')

# Connect to Milvus
# connections.connect(alias="default", uri=uri, token=token)
connections.connect(
    alias="default",
    uri=uri,
    token=token
)

# Define the schema for Milvus collection
collection_name = "image_embeddings"
collection = Collection(name=collection_name)

index_params = {
    "index_type": "HNSW",
    "metric_type": "L2",
    "params": {
        "M": 256,
        "efConstruction": 1024
    }
}
collection.create_index(field_name="embedding", index_params=index_params)
