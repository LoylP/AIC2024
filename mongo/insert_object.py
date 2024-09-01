import os
import json
from collections import Counter
from pymongo import MongoClient

uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

db = client['obj-detection']
collection = db['object-detection-results']

json_directory = r"F:\\AI Challenge\\AIC2024\\AIC2024\\static\\HCMAI22_MiniBatch1\\Objects"


def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)

                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)

                # Extracting data
                class_entities = data.get('detection_class_entities', [])
                class_labels = data.get('detection_class_labels', [])
                scores = data.get('detection_scores', [])
                boxes = data.get('detection_boxes', [])

                # Filter by score >= 0.5
                filtered_entities = []
                filtered_scores = []
                filtered_boxes = []

                for i, score in enumerate(scores):
                    score_value = float(score)
                    if score_value >= 0.3:
                        filtered_entities.append(class_entities[i])
                        filtered_scores.append(score_value)
                        filtered_boxes.append(boxes[i])

                # Count occurrences of each class entity
                entity_counts = Counter(filtered_entities)

                # Prepare document for MongoDB insertion
                folder_name = os.path.basename(root)  # Get folder name
                # Remove the .json extension
                file_name = os.path.splitext(file)[0]
                full_file_path = f"{folder_name}/{file_name}"

                document = {
                    'Video_id': folder_name,  # Folder name
                    'frame': file_name,  # File name without extension
                    'path': full_file_path,  # Folder name + File name without extension
                    # Count of each entity
                    'detection_class_entities': dict(entity_counts),
                    'detection_scores': filtered_scores,
                    'detection_boxes': filtered_boxes
                }

                # Insert into MongoDB
                collection.insert_one(document)


# Start processing from the base directory
process_directory(json_directory)

print("Total documents inserted:", collection.count_documents({}))
