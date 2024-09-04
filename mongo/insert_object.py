import os
import json
from collections import Counter
from pymongo import MongoClient
from tqdm import tqdm

# MongoDB connection
uri = "mongodb+srv://tranduongminhdai:mutoyugi@cluster0.4crgy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

db = client['obj-detection']
collection = db['object-detection-results']

json_directory = "./object_detection_results/"


def process_directory(directory):
    total_files = sum([len(files) for r, d, files in os.walk(
        directory) if any(f.endswith('.json') for f in files)])

    with tqdm(total=total_files, desc="Processing Files", unit="file") as pbar:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r') as json_file:
                        data = json.load(json_file)  # Load the JSON data

                    # Check if data is a string and parse it as JSON
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            print(
                                f"Error: Could not parse the JSON string in file {file_path}")
                            continue

                    if isinstance(data, list):
                        filtered_entities = []
                        filtered_scores = []
                        filtered_boxes = []

                        for detection in data:
                            if isinstance(detection, dict):
                                score_value = detection.get('confidence', 0)
                                if score_value >= 0.5:
                                    filtered_entities.append(
                                        detection.get('name'))
                                    filtered_scores.append(score_value)
                                    filtered_boxes.append(detection.get('box'))
                            else:
                                print(
                                    f"Warning: Expected a dictionary but got {type(detection)} in file {file_path}")

                        entity_counts = Counter(filtered_entities)

                        folder_name = os.path.basename(root)
                        file_name = os.path.splitext(file)[0]
                        full_file_path = f"{folder_name}/{file_name}"

                        document = {
                            'VideoId': folder_name,
                            'frame': file_name,
                            'path': full_file_path,
                            'class_count': dict(entity_counts),
                            'scores': filtered_scores,
                            'boxes': filtered_boxes
                        }

                        collection.insert_one(document)
                    else:
                        print(
                            f"Error: Expected a list but got {type(data)} in file {file_path}")

                    pbar.update(1)


# Start processing from the base directory
process_directory(json_directory)

print("Total documents inserted:", collection.count_documents({}))
