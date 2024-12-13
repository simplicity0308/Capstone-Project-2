import requests
import json

#hardcoded function to navigate to certain folder within ACC and convert get a json response containing all the items in the folder
def get_hubs(access_token):
    endpoint = 'https://developer.api.autodesk.com/project/v1/hubs'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        hubs_list = response.json()

        with open("hubs_list.json", "w") as file:
            json.dump(hubs_list, file, indent=4)

def get_hubdata(access_token):
    with open("hubs_list.json", "r") as file:
        data = json.load(file)
    hub_id = data["data"][0]["id"]

    endpoint = f'https://developer.api.autodesk.com/project/v1/hubs/{hub_id}/projects'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        hubs_data = response.json()

        with open("hubs_data.json", "w") as file:
            json.dump(hubs_data, file, indent=4)

def get_rootfolder(access_token):
    with open("hubs_data.json", "r") as file:
        data = json.load(file)
    project_id = data["data"][1]["id"]
    root_folder_id = data["data"][1]["relationships"]["rootFolder"]["data"]["id"]

    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{root_folder_id}/contents'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        folder_data = response.json()

        with open("rootfolder_data.json", "w") as file:
            json.dump(folder_data, file, indent=4)

def get_projectfiles(access_token):
    with open("hubs_data.json", "r") as file:
        data = json.load(file)
    project_id = data["data"][1]["id"]

    with open("rootfolder_data.json", "r") as file:
        data_contents = json.load(file)
    root_folder_id = data_contents["data"][3]["id"]

    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{root_folder_id}/contents'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        folder_data = response.json()

        with open("projectfiles_data.json", "w") as file:
            json.dump(folder_data, file, indent=4)

def getfolder(access_token):
    with open("hubs_data.json", "r") as file:
        data = json.load(file)
    project_id = data["data"][1]["id"]

    with open("projectfiles_data.json", "r") as file:
        data_contents = json.load(file)
    root_folder_id = data_contents["data"][3]["id"]

    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{root_folder_id}/contents'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        folder_data = response.json()

        with open("folder_data.json", "w") as file:
            json.dump(folder_data, file, indent=4)

def getfoldercontents(access_token):
    with open("hubs_data.json", "r") as file:
        data_id = json.load(file)
    project_id = data_id["data"][0]["id"]

    with open("folder_data.json", "r") as file:
        data_folder = json.load(file)
    folder_id = data_folder["data"][0]["id"]

    endpoint = f'https://developer.api.autodesk.com/data/v1/projects/{project_id}/folders/{folder_id}/contents'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        folder_contents = response.json()

        with open("../folder_contents.json", "w") as file:
            json.dump(folder_contents, file, indent=4)
    else:
        print('failed')

def extractFileInfo():
    with open("../folder_contents.json", "r") as file:
        with open("../folder_contents.json", "r") as file:
            data = json.load(file)
            # Access the 'included' key directly
            included_items = data.get("included", [])

            # Use a set to track unique combinations of file names and hrefs
            unique_files = set()

            # List to store the final output
            file_info = []

            # Iterate over 'included' items
            for item in included_items:
                # Ensure the item contains 'attributes' and 'extension' (where 'sourceFileName' resides)
                attributes = item.get("attributes", {})
                extension = attributes.get("extension", {})

                # Extract file name
                file_name = None
                if "sourceFileName" in extension.get("data", {}):
                    file_name = extension["data"]["sourceFileName"]

                # Extract href link from the 'storage' relationship
                href = None
                storage_data = item.get("relationships", {}).get("storage", {}).get("meta", {})
                href = storage_data.get("link", {}).get("href")

                # Add to file_info only if both file_name and href exist
                if file_name and href:
                    # Use a tuple to track uniqueness
                    file_tuple = (file_name, href)
                    if file_tuple not in unique_files:
                        unique_files.add(file_tuple)
                        file_info.append({
                            "file_name": file_name,
                            "href": href
                        })

            # Save the unique file info to a JSON file
            with open('file_info_with_hrefs.json', 'w') as f:
                json.dump(file_info, f, indent=4)

            print(f"Extracted and saved {len(file_info)} unique files with hrefs to 'file_info_with_hrefs.json'.")


# if __name__ == '__main__':
    # access_token = auth.get_authorization_code()
    # print("Access token: "+access_token)
    # print("\n")

    # get_hubs(access_token)
    # get_hubdata(access_token)
    # get_rootfolder(access_token)
    # get_projectfiles(access_token)
    # getfolder(access_token)
    # getfoldercontents(access_token)
    # extractFileInfo()