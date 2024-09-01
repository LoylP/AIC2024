from pymongo import MongoClient
import json

uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

db = client['obj-detection']
collection = db['object-detection-results']


def extract_unique_classes(documents):
    """Extracts unique object classes from a list of documents."""
    unique_classes = set()
    for doc in documents:
        # Assuming your documents have a field named 'detection_class_entities'
        # containing a list of detected classes
        for class_entity in doc.get('detection_class_entities', []):
            unique_classes.add(class_entity)
    return list(unique_classes)


# Retrieve all documents from the collection
documents = list(collection.find())

# Extract unique object classes
unique_classes = extract_unique_classes(documents)

# Save unique classes to a JSON file
with open("unique_classes.json", "w") as f:
    json.dump(unique_classes, f)

# Optionally, update the MongoDB collection with the unique classes
# collection.update_one(
#     {},  # Match all documents
#     {"$set": {"unique_detection_classes": unique_classes}}
# )

print("Unique object classes saved to unique_classes.json")

# Close MongoDB connection
client.close()
