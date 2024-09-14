# Create a MongoDB client, open a connection to Amazon DocumentDB as a replica set and specify the read preference as secondary preferred

from pymongo import MongoClient
import sys
import os

uri = os.getenv('MONGO_URI')
client = MongoClient(uri)
# Specify the database to be used
db = client.sample_database

# Specify the collection to be used
col = db.sample_collection

# Insert a single document
col.insert_one({'hello': 'Amazon DocumentDB'})

# Find the document that was previously written
x = col.find_one({'hello': 'Amazon DocumentDB'})

# Print the result to the screen
print(x)

# Close the connection
client.close()
