# Import statements
import os  # For accessing environment variables and interacting with the operating system
from datetime import datetime  # Import datetime to get the current time in the assistant's responses
from dotenv import load_dotenv  # For loading environment variables from a .env file
from langchain_core.runnables import Runnable, RunnableConfig  # Import Runnable and RunnableConfig for managing tool execution flow
from openai import OpenAI  # Import OpenAI API client for interacting with the OpenAI API
from langchain.prompts.chat import ChatPromptTemplate  # Import ChatPromptTemplate for creating structured chat prompts
from langchain_openai import ChatOpenAI  # Import ChatOpenAI to initialize a connection to the OpenAI API using Langchain
import tools.embeddings as user  # Import user-defined tool functions for downloading files

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
            "You will use vector embeddings to assist with matching user input to file names or file extensions and guide the user through the file download process."
            "If the user is unsure about the file name you may use file extensions such as .pdf, .jpg, .docx to search through available files, the file embeddings also include the file extension."
            "The embeddings for file names have already been created. If the user query does not match any file names, ask the user to enter another file name."
            "When passing in JSON responses into tools from state, ensure you do **not omit any details** and that you **parse the entire JSON** response fully. "
            "Ensure that any data you output comes from **all the details in the JSON response**, even if that means referencing deeply nested fields. "
            "Before calling tools, ask for an access token"
            "You are capable of using the following tools to accomplish tasks when required:"
            "\n- agent_get_embeddings(): Converts user input into embeddings and retuns a file href url if a matching file is found."
            "\n- agent_get_url(): Generate a signed URL for downloading a specific file."
            "\n\nProcess Overview for File Download:\n"
            "1. **Get File Name**: Obtain the file name or identifying details from the user. The file name may be similar or exactly the same as the target file."
            "2. **Convert File Name To Embeddings and compare embeddings**: Convert the obtained file name from user to embeddings and compare it with embeddings of the available file names using 'agent_get_embeddings()'"
            "3. **Generate Download URL**: Once the closest matching file is identified, use `agent_get_url()` to generate a signed URL for downloading the selected file."
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
    user.agent_get_embeddings,
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




