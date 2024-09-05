from pymongo import MongoClient
import json

# MongoDB URI
uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

# Access the database and collection
db = client['obj-detection']
collection = db['object-detection-results']


def extract_unique_classes(documents):
    """Extracts unique object classes from a list of documents."""
    unique_classes = set()

    for doc in documents:
        # Ensure 'class_count' exists and is a dictionary
        class_count = doc.get('class_count', {})
        if isinstance(class_count, dict):
            # Add each object class (the keys of the class_count dictionary) to the set
            unique_classes.update(class_count.keys())

    return list(unique_classes)


# Retrieve all documents from the collection
documents = list(collection.find())

# Extract unique object classes
unique_classes = extract_unique_classes(documents)

# Save unique classes to a JSON file
with open("unique_classes.json", "w") as f:
    json.dump(unique_classes, f)

print(f"Unique object classes saved to unique_classes.json: {unique_classes}")

# Close MongoDB connection
client.close()
