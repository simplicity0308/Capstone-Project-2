# Import statements
import os  # For accessing environment variables and interacting with the operating system
import requests  # For making HTTP requests
import base64  # For encoding client ID and client secret in base64
from dotenv import load_dotenv  # For loading environment variables from a .env file
from selenium import webdriver  # For automating web browser interactions with Selenium
from selenium.webdriver.common.by import By  # For locating elements in the web page
from selenium.webdriver.support import expected_conditions as EC  # For waiting until elements are visible or clickable
from selenium.webdriver.support.wait import WebDriverWait  # For waiting a specific amount of time for an element
from urllib.parse import urlparse, parse_qs  # For parsing URLs and extracting query parameters
from openai import OpenAI # For interacting with OpenAI API


# Load environment variables
load_dotenv()

# Retrieve credentials from environment variables for Autodesk Construction Cloud
client_id = os.getenv('ACC_CLIENT_ID')
client_secret = os.getenv('ACC_CLIENT_SECRET')
redirect_uri = os.getenv('REDIRECT_URI')
account_email = os.getenv('ACCOUNT_EMAIL')
account_password = os.getenv('ACCOUNT_PASSWORD')
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Setup for base64 encoding of client_id and client_secret
concat = f"{client_id}:{client_secret}"
b64_decode = base64.b64encode(concat.encode("utf-8")).decode("utf-8")

# URLs for token and authorization endpoints
token_url = 'https://developer.api.autodesk.com/authentication/v2/token'
auth_url = f"https://developer.api.autodesk.com/authentication/v2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=data:create%20data:read%20data:write"

# Function to retrieve authorization code from ACC with automation
def get_authorization_code() -> str:
    driver = webdriver.Chrome()
    driver.get(auth_url)
    try:
        # Automate email and password entry
        email_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "userName")))
        email_input.send_keys(account_email)

        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "verify_user_btn")))
        next_button.click()

        password_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password")))
        password_input.send_keys(account_password)

        sign_in_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
        sign_in_button.click()

        # Grant permission
        allow_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "allow_btn")))
        allow_button.click()

        # Wait for the redirect URI with the authorization code
        WebDriverWait(driver, 10).until(lambda d: "code=" in d.current_url)
        redirected_url = driver.current_url

        # Extract the authorization code from the URL
        parsed_url = urlparse(redirected_url)
        authorization_code = parse_qs(parsed_url.query).get("code", [None])[0]

    finally:
        driver.quit()

    return auth_token_v3(authorization_code)

# Function to retrieve access token from ACC using an authorization code
def auth_token_v3(authorization_code):

    # Prepare headers for the POST request (basic authentication using the base64-encoded client ID and secret)
    headers = {
        'Authorization': f'Basic {b64_decode}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Prepare the data for the POST request (authorization code grant type)
    data = {
        'grant_type': 'authorization_code',
        'code': f'{authorization_code}',
        'redirect_uri': f'{redirect_uri}',
    }

    # Send the POST request to exchange the authorization code for an access token
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        # Access token response
        access_token = response.json().get('access_token')
        return access_token
    else:
        print("Failed to retrieve token:", response.status_code, response.text)
        return None

