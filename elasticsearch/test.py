from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import dotenv
import os

# Load environment variables
dotenv.load_dotenv()

# AWS credentials
region = 'ap-southeast-1'
service = 'es'  # OpenSearch is identified as 'es'
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
host = 'search-aic-ocr-7bfs75oseh5ep5dbwjenysalwa.ap-southeast-1.es.amazonaws.com'

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
    connection_class=RequestsHttpConnection
)

index_name = 'python-test-index'
index_body = {
    'settings': {
        'index': {
            'number_of_shards': 2
        }
    }
}

response = client.indices.create(index_name, body=index_body)
print('\nCreating index:')
print(response)

document = {
    'title': 'Moneyball',
    'director': 'Bennett Miller',
    'year': '2011'
}
id = '1'

response = client.index(
    index=index_name,
    body=document,
    id=id,
    refresh=True
)

print('\nAdding document:')
print(response)
