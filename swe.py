from dotenv import load_dotenv
import os
from openai import OpenAI
import re
import datetime
import subprocess

# from ask_gpt import simple_ask_gpt
# Load environment variables from the .env file
load_dotenv()


class SoftwareEngineer:
    protocals = None
    protocals_db = None
    def __init__(self):
        from system import get_db
        # Initialize database connection
        db = get_db()

        # Define collections
        self.protocals_db = db['protocals']


    def get_all_protocols(self):
        """Retrieve all protocol details from MongoDB."""
        self.protocals = list(self.protocals_db.find())
        if self.protocals:
            print(f"Retrieved {len(self.protocals)} protocols from MongoDB")
            return self.protocals
        else:
            print("No protocols found")
            return None
    def get_all_protocol_names(self):
        """
        Retrieve all protocol names from MongoDB and return them as a comma-delimited string.
        
        :return: Comma-delimited string of all protocol names.
        """
        try:
            # Retrieve all protocols from the database
            protocols = list(self.protocals_db.find({}, {"name": 1, "_id": 0}))  # Only return the "name" field
            
            # Extract the names
            protocol_names = [protocol['name'] for protocol in protocols]
            
            # Join the names with commas and return as a string
            return ', '.join(protocol_names)
        
        except Exception as e:
            print(f"Error occurred while fetching protocol names: {e}")
            return None
    def create_protocol(self, protocol_name, description, intent_type, code, verified, tags):
        """Create and store a new protocol in MongoDB."""
        # Create the protocol document
        protocol_document = {
            "name": protocol_name,
            "description": description,
            "swe_intent": intent_type,
            "code": code,
            "verified": verified,
            "tags": []  # You can add custom tags as needed
        }

        # Insert the document into MongoDB
        result = self.protocals_db.insert_one(protocol_document)

        if result.inserted_id:
            print(f"Protocol '{protocol_name}' successfully created and stored in MongoDB.")
            return result.inserted_id
        else:
            print(f"Failed to create protocol '{protocol_name}'.")
            return None
    def find_protocol_by_name(self, protocol_name):
        """
        Find and return a protocol from MongoDB by its name.
        
        :param protocol_name: The name of the protocol to find.
        :return: The protocol document if found, None otherwise.
        """
        protocol = self.protocals_db.find_one({"name": protocol_name})
        
        if protocol:
            print(f"Protocol '{protocol_name}' found: {protocol}")
            return protocol
        else:
            print(f"Protocol '{protocol_name}' not found.")
            return None
    
    def run_protocol_by_name(self, protocol_name):
        """Find a protocol by name and execute the code associated with it."""
        # Find the protocol
        protocol = self.find_protocol_by_name(protocol_name)

        if protocol:
            # Extract the code
            code_to_run = protocol['code']
            
            try:
                exec(code_to_run)
            except Exception as e:
                print(f"Error occurred while running the protocol '{protocol_name}': {e}")
        else:
            print(f"Protocol '{protocol_name}' not found. Cannot execute code.")
    def classify_protocal(self, name):
        print(name)
        # classify
    def generate_protocol_description(self, user_input):
        """
        Generates a short, succinct, and informative description for a new protocol using ChatGPT.
        
        :param user_input: The user input for which a protocol needs to be created.
        :return: A concise, paragraph-style description generated by ChatGPT.
        """
        from ask_gpt import simple_ask_gpt

        try:
            # Refined prompt for a more succinct and paragraph-oriented description
            description_prompt = (
                f"Provide a short, concise protocol description for '{user_input}' in software engineering. "
                f"The description should be a single, informative paragraph that covers the purpose, general approach, and any key considerations. "
                f"Keep the response succinct, focused, and avoid unnecessary detail."
            )
            description = simple_ask_gpt(description_prompt)

            return description
        except Exception as e:
            print(f"Error generating description for '{user_input}': {e}")
            return "No description available."




    def generate_protocol_code(self, user_input):
        """
        Generates Python code for a new protocol using ChatGPT.
        
        :param user_input: The user input for which code needs to be generated.
        :return: Python code generated by ChatGPT, which can be run from a string.
        """
        from ask_gpt import simple_ask_gpt

        try:
            structured_prompt = "You are a software engineer generating only plain Python function code with necessary comments. Provide no extra text or formatting characters. " + f"Generate only the Python function code for the following task: '{user_input}'. " +  " Do not include any additional explanations, text, or code block formatting like backticks. " + "The response should be plain Python code with necessary comments only." +" Make sure to include a correct calling of the function at the end, so your code actually runs."
            

    
            code = simple_ask_gpt(structured_prompt)
            print(code,"CODE")

            # Ensure the response is strictly code with no additional text
            if "def" in code or "class" in code:  # Check for the presence of valid Python code
        
                return code
            else:
                raise ValueError("Generated content is not valid Python code.")
        
        except Exception as e:
            print(f"Error generating code for '{user_input}': {e}")
            return "No code available."


    def handle_input(self, user_input):
        """
        Handle user input by finding or dynamically creating a protocol using ChatGPT for additional information.
        :param user_input: The input command provided by the user.
        """
        # Try to find the protocol by name
        protocol = self.find_protocol_by_name(user_input)

        if protocol:
            # If protocol is found, run the code or return it
            self.run_protocol_by_name(user_input)
        else:
            # If no protocol is found, dynamically create one
            print(f"Protocol '{user_input}' not found. Let's generate a new protocol using ChatGPT.")
            
            # Step 1: Generate the description using the dedicated function
            description = self.generate_protocol_description(user_input)

            # Step 2: Generate the Python code using the dedicated function
            code = self.generate_protocol_code(user_input)

            # Step 3: Define other fields for the new protocol
            new_protocol_name = user_input  # Use the input as the protocol name
            intent_type = "Software Engineering"  # You can modify this depending on your context
            tags = ["dynamically created"]  # Tag as dynamically created for future reference
            verified = False  # Mark as unverified for now

            # Step 4: Create and store the new protocol in MongoDB
            self.create_protocol(new_protocol_name, description, intent_type, code, verified, tags)

            print(f"New protocol '{new_protocol_name}' created successfully!")

            # Optionally, run the code after creation
            try:
                exec(code)
            except Exception as e:
                print(f"Error executing generated code for '{user_input}': {e}")






 


# class SoftwareEngineer:
#     def __init__(self):
#         self.client = 'yes'
       

#     def handle_swe_input(self, userSaid, jarvis_input, jarvis_output):
#         from ask_gpt import classify_intent
#         from system import openai_client
#         should_store= False
#         # start software engineering
#         swe_protocal = classify_intent(
#             userSaid, ["Create Code", "Work on Existing Project", "Create Project", "Get Advice"])
#         response =""
#         if (swe_protocal == "Create Code"):
#             print("create code")
#             response='On it, sir'
#         elif (swe_protocal == "Get Advice"):
#             messages = [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are J.A.R.V.I.S., an intelligent assistant modeled after the AI from the Iron Man movies. "
#                     "Your specific task is to provide Owen with high-level software engineering advice. "
#                     "You are an expert in code optimization, software architecture, and best practices, and you should guide Owen in strategic decision-making. "
#                     "Your responses must be concise, clear, and conversational—never using structured formatting. Therefore, there should be NO numbered lists, bullet points, or code snippets. "
#                     "Speak naturally, as though you're having a professional conversation with a highly skilled developer. "
#                     "Always focus on meaningful, actionable advice that helps Owen think critically and make informed choices without unnecessary detail or technical jargon. "
#                     "Keep the tone confident, friendly, and conversational, ensuring every word serves a purpose and adds value to the conversation."
#                 )
#             },
#             {"role": "user", "content": userSaid}
#         ]

#             completion = openai_client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=messages
#             )

#             # Return the content of the assistant's response
#             response = completion.choices[0].message.content
#             should_store= True
#         elif (swe_protocal == "Work on Exiting Project"):
#             print("Work on Existing Project")
#             response = "on it sir"
#         elif (swe_protocal == "Create Project"):
#             self.create_project_protocol(userSaid, jarvis_input, jarvis_output)
#             response='On it, sir'
#         else:
#             print("nothing")
#             response='On it, sir'
#         return response,should_store

#     def generate_command_with_gpt(self, project_name, description, project_type, frameworks, directory):
#         from ask_gpt import simple_ask_gpt

#         # Construct a more generic prompt to handle various types of project creation commands
#         prompt = (
#             f"Generate a terminal command to create a new project with the following details:\n"
#             f"Project Name: {project_name}\n"
#             f"Description: {description}\n"
#             f"Project Type: {project_type}\n"
#             f"Frameworks: {frameworks}\n"
#             f"Directory: {directory}\n"
#             "Ensure the command uses the latest and correct tools, syntax, and conventions for creating such a project. "
#             "The command should be executable in a terminal and avoid deprecated commands or unsupported options.\n"
#             "If a tool is deprecated or not suited for the context, suggest an alternative or updated tool. "
#             "Only include options that are valid for the command or tool being used, and omit any options that are not supported, such as --description if it is not allowed. "
#             "Do not include any backticks, the word 'bash,' or any additional explanation. "
#             "Only provide the terminal command as plain text."
#         )

#         # Call the GPT function to get the command
#         command = simple_ask_gpt(prompt).strip()

#         # Check if the generated command is 'None' and handle the error
#         if command == "None":
#             raise ValueError(
#                 "Unable to generate a valid terminal command based on the provided details.")

#         print(f"Generated Command: {command}")
#         return command

#     def validate_command_with_gpt(self, command):
#         """
#         Validates the generated terminal command using GPT to ensure it is formatted correctly.
#         If incorrect, requests GPT to provide a corrected version of the command.
#         """
#         from ask_gpt import simple_ask_gpt

#         # Prompt GPT to validate and, if necessary, correct the command
#         validation_prompt = (
#             f"Check if the following terminal command is correctly formatted and valid:\n"
#             f"{command}\n"
#             "If the command is valid and executable, return it exactly as it is. "
#             "If there are any errors or formatting issues, return the corrected command without any explanation. "
#             "Be very strict and only return the terminal command that should be used."
#         )

#         # Call the GPT function to validate and potentially correct the command
#         corrected_command = simple_ask_gpt(validation_prompt).strip()

#         # If the corrected command is different from the original, print the correction
#         if corrected_command != command:
#             print(f"Command corrected by GPT: {corrected_command}")

#         return corrected_command

#     def execute_command(self, command):
#         """
#         Executes the generated command in the terminal.
#         """
#         try:
#             # Run the command in the terminal
#             result = subprocess.run(
#                 command, shell=True, check=True, text=True, capture_output=True)
#             print(f"Command executed successfully: {result.stdout}")
#         except subprocess.CalledProcessError as e:
#             print(f"An error occurred: {e.stderr}")

#     def create_project_protocol(self, userSaid, jarvis_input, jarvis_output):
#         from file_system import handle_file_system
#         from ask_gpt import simple_ask_gpt
#         project_details = {}

#         # Step 2: Continuously prompt GPT for missing information
#         while not project_details.get('project_name'):
#             new_input = jarvis_input(
#                 "What should be the name of this project, sir.")
#             project_details['project_name'] = simple_ask_gpt(
#                 f"Extract the project name from the input: '{new_input}'. "
#                 "Return only the project name or 'None' if it cannot be determined."
#                 .format(userSaid)
#             )

#         while not project_details.get('project_description'):
#             new_input = jarvis_input(
#                 "How would you describe this project, sir?")
#             project_details['project_description'] = simple_ask_gpt(
#                 f"Provide a brief, clear description of the project based on the input: '{new_input}'. "
#                 "Ensure the description is meaningful and relevant. "
#                 "Return a description or 'None' if it cannot be determined."
#                 .format(userSaid)
#             )

#         while not project_details.get('project_type'):
#             new_input = jarvis_input(
#                 "What type of app is this? mobile app? web app?")
#             project_details['project_type'] = simple_ask_gpt(
#                 f"Identify the type of project (e.g., web app, mobile app) from the input: '{new_input}'. "
#                 "Return the type or 'None' if it cannot be determined."
#                 .format(userSaid)
#             )

#         while not project_details.get('framework'):
#             new_input = jarvis_input("What technology stack are you using?")
#             project_details['framework'] = simple_ask_gpt(
#                 f"Identify the framework(s) used in this project (e.g., React, Django) based on the input: '{new_input}'. "
#                 "You must return the name of each framework separated by a comma and a space (e.g., 'React, Django'). "
#                 "If no framework can be determined, return exactly the word 'None'. "
#                 "Do not include any additional words, explanations, or punctuation."
#             )

#         while not project_details.get('directory'):
#             new_input = jarvis_input("What directory ")
#             project_details['directory'] = handle_file_system(
#                 "Get the directory path for "+new_input, intent="Get Directory")

#         # while project_details.get('github_repo') is None:
#         #     new_input = jarvis_input()
#         #     github_repo_response = simple_ask_gpt(
#         #         f"Decide if a GitHub repository is required for this project from the input: '{new_input}'. "
#         #         "Return 'yes' or 'no', or 'None' if it cannot be determined."
#         #         .format(userSaid)
#         #     )
#         #     project_details['github_repo'] = github_repo_response.strip().lower() in [
#         #         'yes', 'y']
#         terminal_command = self.generate_command_with_gpt(project_details["project_name"], project_details["project_description"],
#                                                           project_details["project_type"], project_details["framework"], project_details["directory"])
#         corrected_command = self.validate_command_with_gpt(terminal_command)
#         self.execute_command(corrected_command)
#         return "Created, sir"

#     def create_file(self, description: str, file_name: str = "test.py"):
#         """
#         Generate the Python function and its test function, concatenate them into a single file,
#         save the file, and run the tests to ensure they pass.

#         Args:
#             description (str): The description or task for which the function code is to be generated.
#             file_name (str): The name of the file where the combined code will be saved. Defaults to 'test.py'.

#         Returns:
#             str: The combined code if tests pass, otherwise "cannot make code".
#         """
#         # Generate the main function code
#         generated_code = self.function_creator(description)
#         function_name = self.extract_function_name(generated_code)

#         # Generate the test function for the above code
#         test_code = self.create_test_function(description, file_name)

#         # Concatenate both the function and test code into one file
#         combined_code = generated_code + "\n\n" + test_code

#         # Save the combined code to the specified file
#         with open(file_name, 'w') as file:
#             file.write(combined_code)

#         print(f"Combined function and test code saved to {file_name}")

#         # Run the tests and check if they pass
#         result = subprocess.run(['python3', file_name],
#                                 capture_output=True, text=True)

#         if result.returncode == 0:
#             print("All tests passed successfully.")
#             return combined_code
#         else:
#             print("Tests failed. Cannot make code.")
#             return "Cannot create code"

#     def function_creator(self, prompt: str, ) -> str:
#         """
#         Generate a Python function based on a given prompt using GPT-4o-mini or a similar model
#         and save it to a file.

#         Args:
#             prompt (str): The description or task for which the function code is to be generated.
#             file_name (str): The name of the file where the generated function will be saved. Defaults to 'test.py'.

#         Returns:
#             str: The generated Python function as a string.
#         """
#         # Define the specific model you are using
#         model = "gpt-4o-mini"  # Replace with the appropriate model if needed

#         # Create a structured prompt for generating the function
#         structured_prompt = (
#             f"Generate only the Python function code for the following task: '{prompt}'. "
#             "Do not include any additional explanations, text, or code block formatting like backticks. "
#             "The response should be plain Python code with necessary comments only."
#         )

#         # Define the messages for the GPT model
#         messages = [
#             {"role": "system", "content": "You are a software engineer generating only plain Python function code with necessary comments. Provide no extra text or formatting characters."},
#             {"role": "user", "content": structured_prompt}
#         ]

#         # Make the call to the GPT model to generate the function
#         response = openai_client.chat.completions.create(
#             model=model,
#             messages=messages
#         )

#         # Extract the generated function from the response
#         generated_function = response.choices[0].message.content
#         return generated_function

#     def create_test_function(self, prompt: str, function_name: str,) -> str:
#         """
#         Generate a Python test function for a given prompt using GPT-4o-mini or a similar model
#         and save it to a file.

#         Args:
#             prompt (str): The description or task for which the function code is to be tested.
#             file_name (str): The name of the file where the generated test function will be saved. Defaults to 'test_function.py'.

#         Returns:
#             str: The generated Python test function as a string.
#         """
#         # Define the specific model you are using
#         model = "gpt-4o-mini"  # Replace with the appropriate model if needed

#         # Create a structured prompt for generating the test function
#         structured_prompt = (
#             f"Generate only the Python test code using the unittest module for the function described in this task: '{prompt}'. "
#             f"Do not implement the function itself. Assume the function '{function_name}' already exists and it written before your code. "
#             "Include multiple test cases that use assertions to check correct functionality, handle edge cases, and ensure coverage of various scenarios. "
#             "Provide no explanations or formatting characters, just the plain Python test code."
#         )

#         # Define the messages for the GPT model
#         messages = [
#             {"role": "system", "content": "You are a software engineer generating only plain Python test code using unittest. Provide no extra text or formatting characters."},
#             {"role": "user", "content": structured_prompt}
#         ]

#         # Make the call to the GPT model to generate the test function
#         response = openai_client.chat.completions.create(
#             model=model,
#             messages=messages
#         )

#         # Extract the generated test function from the response
#         generated_test_function = response.choices[0].message.content

#         return generated_test_function

#     def extract_function_name(self, code: str) -> str:
#         """
#         Extract the function name from the generated Python code.

#         Args:
#             code (str): The generated Python code.

#         Returns:
#             str: The name of the function.
#         """
#         # Use a regular expression to find the function name after 'def' and before '('
#         match = re.search(r'def\s+(\w+)\s*\(', code)
#         if match:
#             return match.group(1)
#         return None  # Return None if no function name is found
