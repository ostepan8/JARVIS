import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class SoftwareEngineer:
    def __init__(self, project_directory=None):
        from system import openai_client
        
        self.client = openai_client
        self.command_map:dict = {
            'create file': self.create_new_file,
            'create directory': self.create_new_directory,
            'create and test file': self.create_and_test_file,
            'modify file': self.modify_file,
            'modify and test file': self.modify_and_test_file,
            'test file': self.run_tests,
            'change working directory': self.change_project,
            'get working directory': self.get_working_directory,
            # Add more commands as needed
        }
        

        # Set up the project directory
        self.project_root = os.path.expanduser('~/Desktop')
        if project_directory is None:
            # Default to '~/Desktop/Projects'
            self.project_directory = os.path.expanduser('~/Desktop/Projects')
        else:
            self.project_directory = os.path.abspath(project_directory)

        # Ensure the project directory exists
        os.makedirs(self.project_directory, exist_ok=True)

        print(f"SoftwareEngineer initialized with project directory at {self.project_directory}")

    # used nlp to select a specific function
    def handle_input(self, text:str, jarvis_input, jarvis_output):
        from ask_gpt import classify_intent
        intent: str = classify_intent(text, list(self.command_map.keys()), context_message="")
        if(intent is not "get working directory"):
            jarvis_output("Working on it, sir.")
        response = self.command_map[intent](text)
        
        return response, False
    def create_new_directory(self, text):
        from ask_gpt import simple_ask_gpt
        response = simple_ask_gpt(f"Given the command '{text},' what should the name of the directory be called. ONLY RETURN THE NAME OF THE DIRECTORY")
        full_directory = self.make_new_directory(name = response)
        return f"Created new directory {full_directory}."

    def make_new_directory(self, name):
            try:
                # Create the full path by joining the project root and the new directory name
                full_path = os.path.join(self.project_directory, name)
                original_path = full_path
                count = 1

                # Increment the directory name if it already exists
                while os.path.exists(full_path):
                    full_path = f"{original_path}_{count}"
                    count += 1

                os.makedirs(full_path)
                print(f"Directory '{full_path}' created successfully.")
                
                # Return the full path of the directory
                return full_path
            except Exception as e:
                print(f"An error occurred while creating the directory: {e}")
                return None
        

    def get_working_directory(self, userSaid: str):
        from ask_gpt import simple_ask_gpt
        return simple_ask_gpt(f'Respond succintly and professionally to this prompt: "'+ userSaid +f'" knowing that the working/project directory is "{self.project_directory}"')



    def change_project(self, userSaid: str):
        """
        Changes the current project directory to a specific project or subdirectory within the Desktop,
        allowing flexible navigation to any subdirectory within the Desktop, even deeply nested ones.

        Args:
            userSaid (str): The name or partial name of the project or directory to switch to.

        Returns:
            None

        Raises:
            ValueError: If no matching directory is found.
            OSError: If an error occurs when changing the directory.
        """
        import os
        from ask_gpt import simple_ask_gpt
    

        # Prompt GPT to extract the specific directory name without additional text
        prompt = (
            f"Given the following command, extract and return only the name of the directory "
            f"the user intends to change to. Return only the directory name, without any other text or formatting:\n\n"
            f"User command: '{userSaid}'"
        )
        response = simple_ask_gpt(prompt).strip()
        response_lower = response.lower()
        desktop_path = os.path.expanduser('~/Desktop')

        # Handle the Desktop case
        if response_lower == 'desktop':
            self.project_directory = desktop_path
            print(f"Switched to Desktop at {self.project_directory}")
            return
        else:
            child_path = self.check_immediate_child_exists(response_lower)
            if (child_path is not None):
                self.project_directory = child_path
                print(f"Switched to project: {os.path.basename(self.project_directory)} at {self.project_directory}")
                return

        # Function to recursively search for directories with an exact name match
        def find_directories(base_path, target_name_lower):
            matching_dirs = []
            try:
                with os.scandir(base_path) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            entry_name_lower = entry.name.lower()
                            if entry_name_lower == target_name_lower:
                                matching_dirs.append(entry.path)
                            else:
                                matching_dirs.extend(find_directories(entry.path, target_name_lower))
            except PermissionError:
                pass  # Skip directories for which we don't have permissions
            return matching_dirs

        # Start searching from the desktop path
        matching_dirs = find_directories(desktop_path, response_lower)

        # Handle results
        if not matching_dirs:
            raise ValueError(f"No directory found matching '{response}'.")
        elif len(matching_dirs) == 1:
            # One match found, change to that directory
            self.project_directory = matching_dirs[0]
            print(f"Switched to project: {os.path.basename(self.project_directory)} at {self.project_directory}")
        else:
            # Multiple matches found, print options for the user to choose from
            print(f"Multiple directories found matching '{response}':")
            for idx, path in enumerate(matching_dirs, start=1):
                print(f"{idx}. {path}")

            # Prompt user to select one of the matches
            try:
                choice = int(input("Enter the number of the directory you wish to select: ")) - 1
                if 0 <= choice < len(matching_dirs):
                    self.project_directory = matching_dirs[choice]
                    print(f"Switched to project: {os.path.basename(self.project_directory)} at {self.project_directory}")
                else:
                    raise ValueError("Invalid selection. Please try again.")
            except (ValueError, IndexError):
                print("Invalid input. No directory changed.")
    def check_immediate_child_exists(self, name):
        # Check if any immediate child of the project root matches the provided name (case insensitive)
        path_to_check = os.path.join(self.project_directory, name)
        immediate_children = os.listdir(self.project_directory)
        
        for child in immediate_children:
            if child.lower() == name.lower():
                return path_to_check
        
        return None






    def read_file(self, file_path):
        """Reads the content of a file within the project directory."""
        full_path = os.path.join(self.project_directory, file_path)
        with open(full_path, 'r') as file:
            content = file.read()
        return content

    def write_new_file(self, file_path=None, content="", user_input=""):
        """
        Writes the given content to a file within the project directory. If the file_path is not specified,
        it prompts GPT to generate an output file name and ensures there are no naming conflicts.
        
        Args:
            file_path (str, optional): The path to the file to be created, relative to the project directory.
                                    If None or an empty string is provided, a file name is generated.
            content (str, optional): The content to write to the file. Defaults to an empty string.
            user_input (str, optional): Additional input to assist GPT in generating a relevant file name.
        
        Returns:
            None
        
        Raises:
            ValueError: If file_path cannot be generated or is still None after attempting.
        """
        
        # AUTO NAMING SYSTEM
        if not file_path:
            prompt = f"Generate a file name based on the following user input: {user_input}. ONLY RETURN THE NAME OF THE FILE AND DO NOT RETURN ANYTHING ELSE."
            from ask_gpt import simple_ask_gpt
            file_path = simple_ask_gpt(prompt).strip()
            print(simple_ask_gpt)
            
            if not file_path:
                raise ValueError("Failed to generate a file path. Please specify a valid file path.")

        # Append a number to the file name if it already exists to avoid naming conflicts
        base_name, extension = os.path.splitext(file_path)
        counter = 1
        full_path = os.path.join(self.project_directory, file_path)

        while os.path.exists(full_path):
            file_path = f"{base_name}_{counter}{extension}"
            full_path = os.path.join(self.project_directory, file_path)
            counter += 1

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write the content to the file
        with open(full_path, 'w') as file:
            file.write(content)
        return file_path





    def ask_gpt_to_fix_code(self, code_content, test_output, code_type="Python"):
        """Prompts ChatGPT to fix code based on test output."""
        prompt = (
            f"The following {code_type} code is failing tests due to errors, possibly related to missing imports or other issues. "
            f"Fix the code so that all tests pass and ensure all necessary import statements are included. "
            f"Return only the fixed {code_type} code without any explanations, comments, or Markdown formatting.\n\n"
            f"Code:\n{code_content}\n\n"
            f"Test output:\n{test_output}"
        )
        messages = [{"role": "user", "content": prompt}]
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return completion.choices[0].message.content

    def create_test_class(self, input_file, code_type="Python"):
        """Creates a test class for the input file and saves it in the project directory."""
        # Step 1: Read the input file content
        file_content = self.read_file(input_file)

        # Extract the filename without extension
        input_file_name = os.path.splitext(os.path.basename(input_file))[0]
        test_file_name = f"{input_file_name}_test.py"

        # Craft a prompt to generate a test class for the input file
        test_prompt = (
            f"Create a {code_type} test class using the unittest framework for the following code. "
            f"Ensure the test cases cover edge cases and typical use cases. "
            f"Include all necessary import statements so that the tests can run without errors. "
            f"Include the necessary boilerplate to run the tests when the script is executed directly. "
            f"Return only the code without any comments or markdown formatting.\n\n"
            f"Here is the code:\n\n{file_content}"
        )

        # Ask GPT to generate the test class
        messages = [{"role": "user", "content": test_prompt}]
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        test_code = completion.choices[0].message.content

        # Write the test code to the project directory
        self.write_new_file(test_file_name, test_code)

        print(f"Test class created and saved to {test_file_name}")

    def run_tests(self, test_file):
        """Runs the test file and returns (tests_passed, test_output)."""
        test_file_path = os.path.join(self.project_directory, test_file)
        try:
            # Run the test file directly
            result = subprocess.run(['python', test_file_path], capture_output=True, text=True, cwd=self.project_directory)
            test_output = result.stdout + "\n" + result.stderr
            if result.returncode == 0:
                print("All tests passed.")
                return True, test_output
            else:
                print("Tests failed.")
                print(test_output)
                return False, test_output
        except Exception as e:
            print(f"Error running tests: {e}")
            return False, str(e)

    def modify_and_test_file(self, input_file, output_file, modification_type, code_type="Python"):
        """Modifies a file, creates tests, runs them, and if they fail, modifies the file and repeats."""
        max_iterations = 5  # To prevent infinite loops
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}")

            # Modify the file
            self.modify_file(input_file, output_file, modification_type, code_type)

            # Create the test class
            self.create_test_class(output_file, code_type)

            # Run the tests
            output_file_name = os.path.splitext(os.path.basename(output_file))[0]
            test_file_name = f"{output_file_name}_test.py"

            tests_passed, test_output = self.run_tests(test_file_name)

            if tests_passed:
                print("Tests passed. Modification complete.")
                break
            else:
                print("Tests failed. Modifying the code to fix issues.")
                # Read the modified code
                file_content = self.read_file(output_file)
                # Ask GPT to fix the code
                fixed_code = self.ask_gpt_to_fix_code(file_content, test_output, code_type)
                # Write the fixed code to the output file
                self.write_new_file(output_file, fixed_code)
                # Continue the loop
        else:
            print("Max iterations reached. Could not fix the code to pass the tests.")

    def create_and_test_file(self, output_file, prompt, code_type="Python"):
        """Creates a new file, creates tests, runs them, and if they fail, modifies the file and repeats."""
        max_iterations = 5  # To prevent infinite loops
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}")

            # Create the new file
            self.create_new_file(output_file, prompt, code_type)

            # Create the test class
            self.create_test_class(output_file, code_type)

            # Run the tests
            output_file_name = os.path.splitext(os.path.basename(output_file))[0]
            test_file_name = f"{output_file_name}_test.py"

            tests_passed, test_output = self.run_tests(test_file_name)

            if tests_passed:
                print("Tests passed. File creation complete.")
                break
            else:
                print("Tests failed. Modifying the code to fix issues.")
                # Read the created code
                file_content = self.read_file(output_file)
                # Ask GPT to fix the code
                fixed_code = self.ask_gpt_to_fix_code(file_content, test_output, code_type)
                # Write the fixed code to the output file
                self.write_new_file(output_file, fixed_code)
                # Continue the loop
        else:
            print("Max iterations reached. Could not fix the code to pass the tests.")

    def modify_file(self, userSaid):
        """Reads a file, prompts ChatGPT to modify code based on the given modification type, and writes the response to a new file."""

        # Get all files in the directory (non-recursive)
        all_files = [f for f in os.listdir(self.project_directory) if os.path.isfile(os.path.join(self.project_directory, f))]

        # Join the file names into a comma-separated string
        comma_delimited_files = ', '.join(all_files)

        print(comma_delimited_files)
        from ask_gpt import simple_ask_gpt
        input_file = simple_ask_gpt(f"Given that the user is trying to modify a file with this command: {userSaid}, please generate name of the input file to modify out of this list: {comma_delimited_files}. RETURN ONLY THE NAME OF THE FILE.")

        # Step 1: Read the file
        file_content = self.read_file(input_file)



        prompt = (
            f"Analyze the following code and make the following changes: {userSaid}. "
            f"Ensure that all necessary import statements are included so that the code can run without errors. "
            f"Return only the modified code without any explanations, comments, or Markdown formatting. "
            f"Do not include backticks, comments, or any other text. "
            f"Just return the code:\n\n"
            f"{file_content}"
        )
        code = simple_ask_gpt(prompt)
        # Step 3: Write the modified code to the new file
        self.write_new_file(input_file, code)

        print(f"Code has been modified and saved to {input_file}")

    def create_new_file(self, prompt,):
        """Generates a new file based on a user-provided prompt."""
        from ask_gpt import simple_ask_gpt
        

        final_prompt = (
            f"Generate the main content for a file based on the following prompt: '{prompt}'. "
            f"Ensure the response includes all necessary components (e.g., imports for code, headers for LaTeX, etc.) "
            f"so that the content is complete and functional without any modifications. "
            f"Return only the raw content suitable for the specified type of file, such as code, LaTeX, or plain text. "
            f"Do not include any explanations, comments, Markdown formatting, or backticks. "
            f"Provide only the content of the file."
        )
        new_code = simple_ask_gpt(final_prompt)

        # Write the generated code to the new file
        file_path = self.write_new_file(None, content= new_code, user_input=prompt)
        return "Created file "+ file_path
