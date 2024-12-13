# Import statements
import os  # For accessing environment variables and interacting with the operating system
from datetime import datetime  # Import datetime to get the current time in the assistant's responses
from dotenv import load_dotenv  # For loading environment variables from a .env file
from langchain_core.runnables import Runnable, RunnableConfig  # Import Runnable and RunnableConfig for managing tool execution flow
from openai import OpenAI  # Import OpenAI API client for interacting with the OpenAI API
from langchain.prompts.chat import ChatPromptTemplate  # Import ChatPromptTemplate for creating structured chat prompts
from langchain_openai import ChatOpenAI  # Import ChatOpenAI to initialize a connection to the OpenAI API using Langchain
import tools.downloadFiles as user  # Import user-defined tool functions for downloading files

# Load .env file
load_dotenv()

# Retrieve OpenAI API key from the .env file
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Retrieve ACC client ID and secret from the .env file
acc_client_id = os.getenv('ACC_CLIENT_ID')
acc_client_secret = os.getenv('ACC_CLIENT_SECRET')

# Initialize the LLM using OpenAI's GPT-4 model via Langchain
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o-mini")

# Define the system message template for the assistant's behavior and instructions
assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant for the Sunway Property, specifically designed to assist users in downloading files from Autodesk Construction Cloud."
            "You are capable of using the following tools to accomplish tasks when required:"
            "When passing in JSON responses into tools from state, ensure you do **not omit any details** and that you **parse the entire JSON** response fully. "
            "Ensure that any data you output comes from **all the details in the JSON response**, even if that means referencing deeply nested fields. "
            "Before calling tools, ask for an access token"
            "\n- agent_get_hubs(): Retrieve a list of hubs available to the user."
            "\n- agent_get_hubdata(): Retrieve the projects under a specific hub."
            "\n- agent_get_rootfolder(): Retrieve the root folder of a specific project."
            "\n- agent_get_foldercontents(): Retrieve the contents of a folder in a project."
            "\n- agent_get_url(): Generate a signed URL for downloading a specific file."
            "\n\nProcess Overview for File Download:\n"
            "1. **Get File Name**: Obtain the file name or identifying details from the user. The file name may be similar or exactly the same as the target file."
            "2. **Locate Hub**: Use `agent_get_hubs()` to retrieve a list of hubs, and confirm with the user which hub contains the file if multiple hubs are found."
            "3. **Identify Project**: Use `agent_get_hubdata()` to retrieve the contents of the specified hub. Confirm with the user which project might contain the target file."
            "4. **Access the Root Folder**: Use `agent_get_rootfolder()` to get the root folder for the selected project."
            "5. **Search Through Folders**: Navigate through folder contents using `agent_get_foldercontents()` to find the target file."
            "   - If multiple files match the user's query, confirm with the user before proceeding."
            "6. **Download File**: Once the file is identified and confirmed with the user, use `agent_get_url()` to generate the download link."
            "\n\nGuidelines During Interaction:\n"
            "- **Clarify Before Tool Execution**: Always confirm with the user before running tools unless explicitly instructed."
            "- **Show Tool Outputs**: After running a tool, display its output or any relevant results for user confirmation."
            "- **Error Handling**: Notify the user of any errors encountered during tool execution and suggest alternative actions."
            "- **Be Persistent**: If the file is not found in initial searches, expand your search or clarify details with the user."
            "- **Assist Broadly**: While your primary task is file download, assist the user with any other relevant queries when appropriate."
            "\n\nResponse Formatting Instructions:\n"
            "- Do not bold or italicize your responses."
            "- Keep your responses clear, concise, and professional."
            "- Notify the user if a task involves multiple steps and update them on progress when appropriate."
            "\n\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Define the available tools that the assistant can use to interact with Autodesk Construction Cloud
tools = [
    user.agent_get_hubs,
    user.agent_get_hubdata,
    user.agent_get_rootfolder,
    user.agent_get_foldercontents,
    user.agent_get_url
]

# Define the Assistant class, which encapsulates the logic for running the tools and generating responses
class Assistant:

    # Initialize the Assistant class with a runnable object (a chain of prompts and tools).
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    # Execute the tool chain and return the response in the required format.
    async def __call__(self, state: dict, config: RunnableConfig):
        result = await self.runnable.ainvoke(state)  # Invoke the runnable asynchronously
        return {"messages": result}  # Return the result as a dictionary with messages

# Combine prompt and tools with LLM
assistant_runnable = assistant_prompt | llm.bind_tools(tools)




