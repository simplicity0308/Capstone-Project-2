from dotenv import load_dotenv
import json
from openai import OpenAI
import os
import aiohttp

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Load JSON file containing file names and hrefs
with open('file_info_with_hrefs.json', 'r') as file:
    data = json.load(file)

# Extract file names to embed
file_names = [item['file_name'] for item in data]  # We'll convert the file names to embeddings

# Function to get embeddings from OpenAI API
def get_embeddings(file_names):
    embeddings = []
    for file_name in file_names:
        response = client.embeddings.create(
            model="text-embedding-3-large",  # Use the model for embeddings
            input=file_name,
            encoding_format="float"  # Specify the encoding format
        )
        # Extract the embedding from the response
        embedding = response.data[0].embedding  # This is how we access the embedding vector
        embeddings.append(embedding)
    return embeddings

# Get embeddings for the file names
embeddings = get_embeddings(file_names)

# Prepare the data with embeddings and file names
embeddings_data = []
for i, item in enumerate(data):
    embeddings_data.append({
        'file_name': item['file_name'],  # Save the file name
        'file_name_embedding': embeddings[i],  # Save the embedding for the file name
        'href': item['href']  # Save the href for each file
    })

# Save the embeddings data with file names and hrefs to a new JSON file
with open('embeddings.json', 'w') as outfile:
    json.dump(embeddings_data, outfile, indent=4)

