from dotenv import load_dotenv
import os
from openai import OpenAI
import re
import subprocess

# from ask_gpt import simple_ask_gpt
# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')

openai_client = None


class SoftwareEngineer:
    def __init__(self):
        self.client = 'yes'
        global openai_client
        openai_client = OpenAI(api_key=openai_api_key)

    def handle_swe_input(self, userSaid, jarvis_input, jarvis_output):
        from ask_gpt import classify_intent
        # start software engineering
        swe_protocal = classify_intent(
            userSaid, ["Create Code", "Work on Existing Project", "Create Project"])
        if (swe_protocal == "Create Code"):
            print("create code")
        elif (swe_protocal == "Work on Exiting Project"):
            print("Work on Existing Project")
        elif (swe_protocal == "Create Project"):
            self.create_project_protocol(userSaid, jarvis_input, jarvis_output)
        else:
            print("nothing")

    def create_project_protocol(self, userSaid, jarvis_input, jarvis_output):
        from file_system import handle_file_system
        from ask_gpt import simple_ask_gpt
        project_details = {}

        # Step 2: Continuously prompt GPT for missing information
        while not project_details.get('project_name'):
            new_input = jarvis_input(
                "What should be the name of this project, sir.")
            project_details['project_name'] = simple_ask_gpt(
                f"Extract the project name from the input: '{new_input}'. "
                "Return only the project name or 'None' if it cannot be determined."
                .format(userSaid)
            )

        while not project_details.get('project_description'):
            new_input = jarvis_input(
                "How would you describe this project, sir?")
            project_details['project_description'] = simple_ask_gpt(
                f"Provide a brief, clear description of the project based on the input: '{new_input}'. "
                "Ensure the description is meaningful and relevant. "
                "Return a description or 'None' if it cannot be determined."
                .format(userSaid)
            )

        while not project_details.get('project_type'):
            new_input = jarvis_input(
                "What type of app is this? mobile app? web app?")
            project_details['project_type'] = simple_ask_gpt(
                f"Identify the type of project (e.g., web app, mobile app) from the input: '{new_input}'. "
                "Return the type or 'None' if it cannot be determined."
                .format(userSaid)
            )

        while not project_details.get('framework'):
            new_input = jarvis_input("What technology stack are you using?")
            project_details['framework'] = simple_ask_gpt(
                f"Identify the framework(s) used in this project (e.g., React, Django) based on the input: '{new_input}'. "
                "You must return the name of each framework separated by a comma and a space (e.g., 'React, Django'). "
                "If no framework can be determined, return exactly the word 'None'. "
                "Do not include any additional words, explanations, or punctuation."
            )

        while not project_details.get('directory'):
            new_input = jarvis_input("What directory ")
            project_details['directory'] = handle_file_system(
                "Get the directory path for "+new_input, intent="Get Directory")

        # while project_details.get('github_repo') is None:
        #     new_input = jarvis_input()
        #     github_repo_response = simple_ask_gpt(
        #         f"Decide if a GitHub repository is required for this project from the input: '{new_input}'. "
        #         "Return 'yes' or 'no', or 'None' if it cannot be determined."
        #         .format(userSaid)
        #     )
        #     project_details['github_repo'] = github_repo_response.strip().lower() in [
        #         'yes', 'y']
        print(project_details)
        return "found"

    def create_file(self, description: str, file_name: str = "test.py"):
        """
        Generate the Python function and its test function, concatenate them into a single file,
        save the file, and run the tests to ensure they pass.

        Args:
            description (str): The description or task for which the function code is to be generated.
            file_name (str): The name of the file where the combined code will be saved. Defaults to 'test.py'.

        Returns:
            str: The combined code if tests pass, otherwise "cannot make code".
        """
        # Generate the main function code
        generated_code = self.function_creator(description)
        function_name = self.extract_function_name(generated_code)

        # Generate the test function for the above code
        test_code = self.create_test_function(description, file_name)

        # Concatenate both the function and test code into one file
        combined_code = generated_code + "\n\n" + test_code

        # Save the combined code to the specified file
        with open(file_name, 'w') as file:
            file.write(combined_code)

        print(f"Combined function and test code saved to {file_name}")

        # Run the tests and check if they pass
        result = subprocess.run(['python3', file_name],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print("All tests passed successfully.")
            return combined_code
        else:
            print("Tests failed. Cannot make code.")
            return "Cannot create code"

    def function_creator(self, prompt: str, ) -> str:
        """
        Generate a Python function based on a given prompt using GPT-4o-mini or a similar model
        and save it to a file.

        Args:
            prompt (str): The description or task for which the function code is to be generated.
            file_name (str): The name of the file where the generated function will be saved. Defaults to 'test.py'.

        Returns:
            str: The generated Python function as a string.
        """
        # Define the specific model you are using
        model = "gpt-4o-mini"  # Replace with the appropriate model if needed

        # Create a structured prompt for generating the function
        structured_prompt = (
            f"Generate only the Python function code for the following task: '{prompt}'. "
            "Do not include any additional explanations, text, or code block formatting like backticks. "
            "The response should be plain Python code with necessary comments only."
        )

        # Define the messages for the GPT model
        messages = [
            {"role": "system", "content": "You are a software engineer generating only plain Python function code with necessary comments. Provide no extra text or formatting characters."},
            {"role": "user", "content": structured_prompt}
        ]

        # Make the call to the GPT model to generate the function
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )

        # Extract the generated function from the response
        generated_function = response.choices[0].message.content
        return generated_function

    def create_test_function(self, prompt: str, function_name: str,) -> str:
        """
        Generate a Python test function for a given prompt using GPT-4o-mini or a similar model
        and save it to a file.

        Args:
            prompt (str): The description or task for which the function code is to be tested.
            file_name (str): The name of the file where the generated test function will be saved. Defaults to 'test_function.py'.

        Returns:
            str: The generated Python test function as a string.
        """
        # Define the specific model you are using
        model = "gpt-4o-mini"  # Replace with the appropriate model if needed

        # Create a structured prompt for generating the test function
        structured_prompt = (
            f"Generate only the Python test code using the unittest module for the function described in this task: '{prompt}'. "
            f"Do not implement the function itself. Assume the function '{function_name}' already exists and it written before your code. "
            "Include multiple test cases that use assertions to check correct functionality, handle edge cases, and ensure coverage of various scenarios. "
            "Provide no explanations or formatting characters, just the plain Python test code."
        )

        # Define the messages for the GPT model
        messages = [
            {"role": "system", "content": "You are a software engineer generating only plain Python test code using unittest. Provide no extra text or formatting characters."},
            {"role": "user", "content": structured_prompt}
        ]

        # Make the call to the GPT model to generate the test function
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )

        # Extract the generated test function from the response
        generated_test_function = response.choices[0].message.content

        return generated_test_function

    def extract_function_name(self, code: str) -> str:
        """
        Extract the function name from the generated Python code.

        Args:
            code (str): The generated Python code.

        Returns:
            str: The name of the function.
        """
        # Use a regular expression to find the function name after 'def' and before '('
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)
        return None  # Return None if no function name is found


# Example usage
if __name__ == "__main__":
    engineer = SoftwareEngineer()
    task_description = "Write a Python function to calculate the factorial of a given non-negative integer."
    engineer.create_file(task_description, "test.py")
