# Import statements
import json  # Import json to handle JSON data format
import os  # For accessing environment variables and interacting with the operating system
import aiohttp  # Import aiohttp for making asynchronous HTTP requests
import numpy as np  # Import numpy for numerical operations
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity to measure similarity between vectors
from urllib.parse import urlparse, unquote  # Import urlparse for parsing URLs and unquote for decoding URL-encoded strings
from dotenv import load_dotenv  # For loading environment variables from a .env file
from langchain_core.tools import tool  # Import the @tool decorator and the tool functionality from Langchain.
from openai import OpenAI  # Import the OpenAI client for interacting with the OpenAI API

# Load .env file
load_dotenv()

# Retrieve OpenAI API key from the .env file
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Function to compare user input embeddings with file name embeddings
@tool
async def agent_get_embeddings(file_name: str):
    """
    Converts the file name or file extension specified by the user to a set of embeddings,
    Compares the embeddings generated from the user's input with the pre-existing embeddings of file names,
    calculates the cosine similarity, and returns the most similar file's download link or a message indicating
    no similar file was found.

    Args:
        file_name (str): The file name specified by the user.

    Returns:
        str: JSON-formatted string of embeddings.
    """

    # Call the OpenAI API to get embeddings for the provided file name
    try:
        # Call the OpenAI API to get embeddings for the provided file name
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=file_name,
        )
        # Extract the embedding vector from the response
        embedding = response.data[0].embedding

        # Load pre-existing embeddings from the JSON file
        embeddings_file_path = "D:/Desktop/CP2/embeddings/embeddings.json"  # Update path if needed
        with open(embeddings_file_path, "r") as file:
            embeddings_data = json.load(file)

            # Initialize variables to track matches
            matches = []

            # Compare the user input's embedding with each stored embedding using cosine similarity
            for entry in embeddings_data:
                stored_embedding = np.array(entry["file_name_embedding"]).reshape(1, -1)
                similarity = cosine_similarity([embedding], stored_embedding)[0][0]

                # Only accept matches above a certain threshold
                if similarity > 0.3:
                    matches.append({
                        'file_name': entry['file_name'],
                        'href': entry['href'],
                        'similarity': similarity
                    })

            # Sort matches by similarity score in descending order
            matches = sorted(matches, key=lambda x: x['similarity'], reverse=True)

            # If no good matches are found
            if not matches:
                return "results: Unfortunately, no file matching your query was found.."

            # Construct response with best matches
            best_results = "best results found:\n"
            hrefs = []

            for match in matches[:3]:  # Return top 3 matches
                best_results += f"{match['file_name']}, Similarity: {match['similarity']:.4f}\n"
                hrefs.append(f"{{{match['file_name']}, href={match['href']}}}")

            # Combine everything into a single string
            return f"{best_results}\n" + "\n\n\n\n".join(hrefs)

    except Exception as e:
        return f"error messages: Error processing request: {str(e)}"


# Tool to retrieve a signed S3 URL of a file from ACC using the the Data Management API
@tool
async def agent_get_url(access_token: str, href: str):
    """
    Retrieves a signed S3 URL of a specific file in a folder based the href link to download the file, as accessible by the current user.

    Args:
        access_token (str): The access token for Autodesk API authentication
        href (str): The link used to download the file from Autodesk.

    Returns:
        str: Signed S3 URL of the file to be downloaded.
    """

    #Parse the provided URL to break it into its components (e.g., scheme, host, path, etc.)
    parsed_url = urlparse(href)

    # Split the path of the URL into parts based on the '/' delimiter.
    path_parts = parsed_url.path.split('/')

    # Extract the 'bucket_key' from the URL path.
    # In this case, it's located at the 4th index of the split path.
    bucket_key = path_parts[4]

    # Extract the 'object_key' from the URL path, starting from the 6th index onwards.
    object_key = '/'.join(path_parts[6:])
    object_key = unquote(object_key)

    # Debug statements to ensure the URL is parsed correctly
    # print("[DEBUG] Bucket Key: "+bucket_key)
    # print("[DEBUG] Object Key: "+object_key)

    # Endpoint URL to fetch the signed S3 URL of the file using the bucket and object keys.
    endpoint = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_key}/objects/{object_key}/signeds3download"

    # Set the authorization header for the HTTP request using the provided access token.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Asynchronously make a GET request to the Autodesk API to fetch the signed S3 URL.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                response_json = await response.json()
                download_url = response_json.get('url', None)
                # download_url = await response.text()
                return f"download URLS: {download_url}"
            else:
                return f"errors: Failed to generate signed download URL."
