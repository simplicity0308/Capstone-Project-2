# Import statements
import os
import aiohttp
from urllib.parse import urlparse, unquote  # To parse URLs and decode URL-encoded strings
from dotenv import load_dotenv  # Load environment variables from a .env file.
from langchain_core.tools import tool  # Import the @tool decorator and the tool functionality from Langchain.
from openai import OpenAI  # Import the OpenAI client for interacting with the OpenAI API

# Load .env file
load_dotenv()

# Retrieve OpenAI API key from the .env file
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)


# Tool to retrieve a list of hubs from ACC using the the Data Management API
@tool
async def agent_get_hubs(access_token: str):
    """
    Retrieves a list of all hubs available in Autodesk Construction Cloud, as accessible by the current user.

    Args:
        access_token (str): The access token for Autodesk API authentication.

    Returns:
        str: JSON-formatted string of hub information based on the provided instruction, or an error message if failed.
    """

    # Endpoint URL to fetch the hubs.
    endpoint = 'https://developer.api.autodesk.com/project/v1/hubs'

    # Set the authorization header for the HTTP request using the provided access token.
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    # Asynchronously make a GET request to the Autodesk API to fetch all the hubs.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                hubs_list = await response.json()

                # Compress the response data to only include type, id, and name
                compressed_data = {
                    "hubs": [
                        {
                            "type": hub.get("type"),
                            "id": hub.get("id"),
                            "name": hub.get("attributes", {}).get("name", "Unnamed Hub")
                        }
                        for hub in hubs_list.get("data", [])
                    ]
                }

                # Return a formatted string with compressed hub list
                return f"list of available hubs, please choose one so I may proceed: \n {', '.join([hub['name'] for hub in compressed_data['hubs']])}" \
                       f"\n\n\n\n\n{compressed_data}"
            else:
                return f"Error: Failed to retrieve hubs: " + str(response.status)

# Tool to retrieve the contents of a specific hub from ACC using the the Data Management API
@tool
async def agent_get_hubdata(access_token: str, hub_name: str, hubs_list: str) -> str:
    """
    Retrieves contents of a specific hub in Autodesk Construction Cloud based on its hub id, as accessible by the current user.

    Args:
        access_token (str): The access token for Autodesk API authentication.
        hub_name (str): Name of the hub, actual hub name can be similar or completely same.
        hubs_list (str): JSON-formatted string of the list of hubs.

    Returns:
        str: JSON-formatted string of hub information based on the provided instruction, or an error message if failed.
    """

    # Prompt for GPT to extract hub_id from the arguments
    prompt = (
        f"The following is a JSON list of hubs:\n"
        f"{hubs_list}\n\n"
        f"{hub_name} can be similar or completely same with the actual hub name needed."
        f"Find the hub with the name {hub_name} and return only its 'id'. No additional text, explanation, or formatting."
        f"Take note that the output should not be encased in quotation marks"
    )

    # Query GPT to extract hub_id
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500
    )

    # Access the response from GPT and retrieve the hub_id
    hub_id = response.choices[0].message.content

    # Endpoint URL to fetch the contents of the hub using the hub ID.
    endpoint = f'https://developer.api.autodesk.com/project/v1/hubs/{hub_id}/projects'

    # Set the authorization header for the HTTP request using the provided access token.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Asynchronously make a GET request to the Autodesk API to fetch hub contents.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                hubs_data = await response.json()

                # Compress the data to only include type, id, and name for each project
                compressed_data = {
                    "projects": [
                        {
                            "type": project.get("type"),
                            "id": project.get("id"),
                            "name": project.get("attributes", {}).get("name", "Unnamed Project"),
                            "projectid": project.get("relationships", {}).get("rootFolder", {}).get("data", {}).get("id")
                        }
                        for project in hubs_data.get("data", [])
                    ]
                }

                # Return a formatted string with compressed project data
                project_names = [project['name'] for project in compressed_data['projects']]
                return f"list of available projects currently within the hub {hub_name}, please choose one so I may proceed: \n {', '.join(project_names)}" \
                       f"\n\n\n\n\n{compressed_data}"
            else:
                return f"error: Failed to retrieve hub data: {response.status}"

# Tool to retrieve the list of root folders from ACC using the the Data Management API
@tool
async def agent_get_rootfolder(access_token: str, project_name: str, hubs_data: str) -> str:
    """
    Retrieves the contents of the root folder for a specific project in Autodesk Construction Cloud based on its project id, as accessible by the current user.

    Args:
        access_token (str): The access token for Autodesk API authentication.
        project_name (str): Name of the project, actual project name can be similar or completely same.
        hubs_data (str): JSON-formatted string of hub information.

    Returns:
        str: JSON-formatted string of folder information based on the provided instruction, or an error message if failed.
    """

    # The prompt asks the model to extract the 'id' of the project based on the project name.
    prompt1 = (
        f"The following is a JSON list of projects:\n"
        f"{hubs_data}\n\n"
        f"{project_name} can be similar or completely same with the actual hub name needed."
        f"Find the project with the name {project_name} and return its 'id'. No additional text, explanation, or formatting."
        f"Take note that the output should not be encased in quotation marks"
    )

    # Query the LLM for the project id based on the provided project name.
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": prompt1},
        ],
        max_tokens=300
    )
    # Access the response and retrieve the project id from the LLM output.
    project_id = response.choices[0].message.content

    # The prompt asks the model to extract the 'projectid' value based on the 'project_id' extracted in the first step.
    prompt2 = (
        f"The following is a JSON list of projects:\n"
        f"{hubs_data}\n\n"
        f"Find the project with the id {project_id} and return the 'projectid' value. No additional text, explanation, or formatting."
        f"Take note that the output should not be encased in quotation marks"
    )

    # Query the LLM again to retrieve the 'projectid' value for the specific project id.
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": prompt2},
        ],
        max_tokens=300
    )
    # Access the response and retrieve the root folder id based on the project id.
    root_folder_id = response1.choices[0].message.content

    # Endpoint URL to fetch the contents of the root folder using the project and root folder IDs.
    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{root_folder_id}/contents'

    # Set the authorization header for the HTTP request using the provided access token.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Asynchronously make a GET request to the Autodesk API to fetch root folder contents.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                folder_data = await response.json()

                # Compress the folder data to include only necessary fields: type, id, folder name, and parent folder id.
                compressed_data = {
                    "folders": [
                        {
                            "type": folder.get("type"),
                            "id": folder.get("id"),
                            "folder_name": folder.get("attributes", {}).get("name", "Unnamed Folder"),
                            "parent_id": folder.get("relationships", {}).get("parent", {}).get("data", {}).get("id")
                        }
                        for folder in folder_data.get("data", [])
                    ]
                }

                # Extract folder names from the 'data' section of the JSON response.
                folder_names = [
                    folder.get("attributes", {}).get("name", "Unnamed Folder")
                    for folder in folder_data.get("data", [])
                ]

                # Join the folder names into a single string, separated by commas.
                formatted_folder_names = ", ".join(folder_names)

                # Return a formatted string with compressed folder data.
                return (f"list of available Root Folders, please choose one from the list: \n{formatted_folder_names}"
                        f"\n \n \n \n \n{project_id}"
                        f"\n{compressed_data}")
            else:
                return f"error: Failed to retrieve root folder: {response.status}"

# Tool to retrieve the contents of a folder from ACC using the the Data Management API
@tool
async def agent_get_foldercontents(access_token: str, project_id: str, folder_name: str, folder_data: str) -> str:
    """
     Retrieves the contents of a folder for a specific project in Autodesk Construction Cloud based on its project id and folder id, as accessible by the current user.

     Args:
         access_token (str): The access token for Autodesk API authentication.
         project_id (str): id of the project, obtained from get_rootfolder() .
         folder_name (str): Name of the folder to be accessed. obtained from user prompt.
         folder_data (str)： JSON-formatted string of folder information.

     Returns:
          str: A formatted string containing the folder contents in the format:
             "Contents of folder: [Name, FileType, ID], ..."
     """

    # The prompt asks the model to extract the 'id' of the folder based on the folder name.
    prompt1 = (
        f"The following is a JSON list of projects:\n"
        f"{folder_data}\n\n"
        f"{folder_name} can be similar or completely same with the actual hub name needed."
        f"Find the project with the name {folder_name} and return its 'id'. No additional text, explanation, or formatting."
        f"Return just the id value, e.g., urn:adsk.wipprod:fs.folder:co.Q04kD3-uT-usBOiCTSKggA."
        f"Do not include curly braces or quotation marks in your response."
    )

    # Query the LLM for the folder id based on the provided folder name.
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": prompt1},
        ],
        max_tokens=300
    )

    # Access the response and retrieve the folder id based on the folder name.
    folder_id = response.choices[0].message.content

    # Debug statements to display project_id and folder_id to ensure LLM is returning correct responses
    # print("[DEBUG] project id: " + project_id)
    # print("[DEBUG] folder id: " + folder_id)

    # Endpoint URL to fetch the contents of the folder using the project and folder IDs.
    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{folder_id}/contents'

    # Set the authorization header for the HTTP request using the provided access token.
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Asynchronously make a GET request to the Autodesk API to fetch folder contents.
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                folder_contents = await response.json()

                # Compress the response
                compressed_data = {
                    "data": [
                        # Compress the folders section (only type, id, name)
                        {
                            "type": item["type"],
                            "id": item["id"],
                            "name": item["attributes"]["name"]
                        }
                        for item in folder_contents.get("data", [])
                        if item["type"] == "folders"  # Only folders
                    ],
                    "included": [
                        # Compress the included section (only id, name, href under storage->meta->link)
                        {
                            "id": item["id"],
                            "file_name": item["attributes"]["name"],
                            "href": item["relationships"]["storage"]["meta"].get("link", "No link available")
                            # Safely get href or fallback
                        }
                        for item in folder_contents.get("included", [])
                        if "storage" in item["relationships"]  # Only items that have a storage field
                    ]
                }

                # Process folder contents
                contents = []
                for item in folder_contents.get("data", []):
                    try:
                        item_name = item["attributes"].get("displayName", "Unnamed")
                        item_type = "folder" if item["type"] == "folders" else "file"
                        contents.append(f"[{item_name}, {item_type}]")
                    except KeyError as e:
                        return f"Error processing item in folder: Missing key {e}"

                # Return a formatted string with compressed folder data.
                return (
                    f"folder contents of {folder_name}, please choose the folder or file you wish to access: \n {', '.join(contents)}"
                    f"\n\n\n\n{compressed_data}")
            else:
                return f"error: Failed to retrieve root folder: {response.status}"

# Tool to retrieve a signed S3 URL of a file from ACC using the the Data Management API
@tool
async def agent_get_url(access_token: str, folder_contents: str, file_name: str) -> str:
    """
    Retrieves a signed S3 URL of a specific file in a folder based on its file name to download the file, as accessible by the current user.

    Args:
        access_token (str): The access token for Autodesk API authentication
        folder_contents (str): JSON list of files within a folder.
        file_name (str): Name of the file to be downloaded.

    Returns:
        str: Signed S3 URL of the file to be downloaded.
    """

    # The prompt asks the model to extract the 'href' of the file based on the file name.
    prompt = (
        f"The following is a JSON list of files within a folder:\n"
        f"{folder_contents}\n\n"
        f"{file_name} can be similar or completely same with the actual hub name needed."
        f"Under attribute 'included', Find the index with the name {file_name} and return only its 'href' value. "
        f"Make sure to return the raw URL, without any extra text, quotation marks, or JSON formatting."
        f"The output should only contain the URL (e.g., https://developer.api.autodesk.com/oss/v2/buckets/wip.dm.prod/objects/... etc.)."
    )

    # Query the LLM for the 'href' value based on the provided file name.
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300
    )
    # Access the response and retrieve the 'href' value.
    file_url = response.choices[0].message.content

    # Debug statement to ensure the 'href' value is correctly retrieved
    # print("[DEBUG]File url: "+file_url)

    #Parse the provided URL to break it into its components (e.g., scheme, host, path, etc.)
    parsed_url = urlparse(file_url)

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

                # Return a formatted string.
                return f"download URL for {file_name} : {download_url}"
            else:
                return f"error: Failed to generate signed download URL."
