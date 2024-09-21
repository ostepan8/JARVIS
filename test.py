import asyncio
from system import initialize
asyncio.run(initialize())  # noqa
from swe import SoftwareEngineer
# Example usage of the create_protocol function
# Create an instance of SoftwareEngineer
software_engineer = SoftwareEngineer()

# Find a protocol by name
protocol_name = "Create Function"
found_protocol = print(software_engineer.handle_input("Create a react native cover screen file on my desktop called 'TitlePage.js'"))


# import subprocess
# from dotenv import load_dotenv
# import os
# import openai  # Import openai properly

# # Load environment variables from the .env file
# load_dotenv()

# openai_api_key = os.getenv('OPENAI_API_KEY')
# openai.api_key = openai_api_key  # Set the OpenAI API key


# def simple_ask_gpt(message):
#     """
#     Sends a message to GPT and returns the response.
#     """
#     messages = [{"role": "user", "content": message}]

#     # Call GPT-4o-mini model or other model specified
#     completion = openai.ChatCompletion.create(
#         model="gpt-4o-mini",
#         messages=messages
#     )

#     # Return the content of the assistant's response
#     return completion.choices[0].message['content']


# def run_mac_command(command):
#     """
#     Runs a terminal command on macOS and prints its output.
#     """
#     try:
#         # Use subprocess to run the command and capture output
#         result = subprocess.run(command, shell=True,
#                                 check=True, text=True, capture_output=True)
#         print(result.stdout)  # Print standard output
#     except subprocess.CalledProcessError as e:
#         print(f"Command execution failed: {e.stderr}")
#         # When command fails, ask GPT for assistance
#         print("Command failed. Asking GPT for help...")
#         gpt_response = simple_ask_gpt(
#             f"Explain how to handle this error: {e.stderr.strip()}")
#         print(f"GPT Response: {gpt_response}")


# def change_to_desktop_parent():
#     """
#     Changes the current working directory to the parent of the 'Desktop' directory.
#     """
#     while True:
#         # Get the current directory
#         current_dir = os.getcwd()

#         # List all directories in the current directory
#         directories = os.listdir(current_dir)

#         # Check if 'Desktop' is in the list of directories
#         if 'Desktop' in directories:
#             # Go one level up from the directory containing 'Desktop'
#             os.chdir('..')
#             print(f"Changed directory to the parent of Desktop: {os.getcwd()}")
#             break

#         # Move one level up in the directory tree
#         os.chdir('..')


# def run_command_at_root(command):
#     """
#     Creates a new file on the Desktop.
#     """
#     change_to_desktop_parent()  # Navigate to the parent of Desktop first

#     # Get the Desktop path to create a file there
#     home_dir = os.path.expanduser('~')
#     desktop_path = os.path.join(home_dir, 'Desktop', file_name)

#     # Check for write permission on the Desktop directory
#     if not os.access(os.path.dirname(desktop_path), os.W_OK):
#         print("Permission denied: Cannot write to the Desktop directory. Please check your permissions.")
#         return

#     # Create a new file on the Desktop
#     try:
#         with open(desktop_path, 'w') as file:
#             # You can modify the content as needed
#             file.write("This is a new file created on the Desktop.")
#         print(f"File '{file_name}' created successfully on the Desktop.")
#     except PermissionError:
#         print(
#             f"Permission denied: Unable to create '{file_name}' on the Desktop. Please check your permissions.")
#     except Exception as e:
#         print(f"Failed to create the file: {e}")


# # Example usage
# if __name__ == "__main__":
#     # Replace with your desired file name
#     create_file_on_desktop("my_new_file.txt")
