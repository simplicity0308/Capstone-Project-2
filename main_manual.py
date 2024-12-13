# Import statements
import os  # For accessing environment variables and interacting with the operating system
import asyncio  # Importing the asyncio module to handle asynchronous operations and event loops in Python.
import json  # Importing the json module for working with JSON
from agents.agent_manual import Assistant, assistant_runnable  # Importing Assistant for interaction
import tools.authentication as auth  # Authentication module to get access tokens
import tools.downloadFiles  # Module to download files
import pyperclip  # To copy access token to clipboard
import tools.formatting as format  # Formatting helper functions for tool outputs

# Main asynchronous function for running the assistant
async def main(access_token):
    print("Access token: " + access_token)

    # Copy the access token to clipboard for easy access
    pyperclip.copy(access_token)

    print("Access token has been copied to the clipboard!")
    print("\n")

    # Initialize the assistant
    assistant = Assistant(assistant_runnable)
    state = {
        "messages": []  # Initialize the messages list to track the conversation
    }

    print("File download assistant (manual), please enter your query or type 'exit' to quit")

    while True:
        # User input from the terminal
        user_input = input("You > ")

        # Exit condition to break the loop
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Add user input to the state for tracking purposes
        state["messages"].append({"role": "user", "content": user_input})

        try:
            # Get response from the assistant by passing the current state
            response = await assistant(state, config={})

            # Extract the assistant's message from the response
            message = response["messages"]
            assistant_message = message.content

            # Check if tool calls are present in the assistant's response
            if "tool_calls" in message.additional_kwargs:
                for tool_call in message.additional_kwargs["tool_calls"]:
                    tool_arguments = tool_call["function"]["arguments"]
                    tool_name = tool_call["function"]["name"]

                    # Parse arguments to pass to the tool
                    args = json.loads(tool_arguments)

                    # Debug statement to verify tool execution
                    # print(f"\n\n [DEBUG] Executing tool: {tool_name} with args: {tool_arguments}")

                    # Dynamically fetch tool function
                    tool_function = getattr(tools.downloadFiles, tool_name, None)

                    # Check if the tool function is callable
                    if callable(tool_function):
                        # Call the tool with the provided arguments asynchronously
                        tool_result = await tool_function.ainvoke(args)

                        # Format the result for display
                        tool_result_display = format.get_first_n_lines(tool_result, n=4)

                        # Debug statement to display full tool result
                        # print(f"[DEBUG] Tool '{tool_name}' executed successfully with result: {tool_result}")

                        # Process the tool result and generate an assistant response
                        assistant_message = f"Here is the {tool_result_display}\n"

                        # Add the tool result to the assistant's message for the next conversation
                        state["messages"].append({"role": "assistant", "content": tool_result})
                    else:
                        raise ValueError(f"Tool '{tool_name}' not found or not callable.")

            # After processing tool calls, add the assistant's message to the state
            print(f"Assistant > {assistant_message}")
            state["messages"].append({"role": "assistant", "content": assistant_message})

        except Exception as e:
            print(f"Error during assistant interaction: {e}")

# Main execution point, calling the authorization function to get the access token
if __name__ == "__main__":
    # Authentication to get the token
    access_token = auth.get_authorization_code()

    # Run the main async function with the token
    asyncio.run(main(access_token))
