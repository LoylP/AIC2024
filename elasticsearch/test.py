import json
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth
import boto3
import dotenv
import os
from tqdm import tqdm

# Load environment variables
dotenv.load_dotenv()

# AWS credentials
region = 'ap-southeast-1'
service = 'aoss'
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
host = '1292lxh5s7786w68m0ii.ap-southeast-1.aoss.amazonaws.com'

# Get AWS credentials using boto3
session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)

# Retrieve temporary credentials
credentials = session.get_credentials().get_frozen_credentials()

# Create AWS4Auth with the temporary credentials
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

# Create an OpenSearch client
client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=60,
    max_retries=5,
    retry_on_timeout=True
)

# Define collection name
collection_name = 'ocr'

# Retrieve sample documents from the collection
search_body = {
    "query": {"match_all": {}},
    "size": 10  # Limit to 10 documents for verification
}

try:
    response = client.search(
        index=collection_name,
        body=search_body
    )
    print('\nSample of indexed documents:')
    for hit in response['hits']['hits']:
        print(hit['_source'])
except Exception as e:
    print('\nSearch error:')
    print(e)