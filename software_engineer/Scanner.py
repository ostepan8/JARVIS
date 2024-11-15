import os

class ProjectScanner:
    projects_mongo_collection = None

    def __init__(self):
        from system import get_db
        db = get_db()
        self.projects_mongo_collection = db['projects']

    def scan_project(self, project_directory: str, command: str):
        """
        Scans the project directory and creates a project instance in MongoDB.
        """
        project_data = self.gather_project_data(project_directory, command)
        print(project_data)
        # self.save_project_to_db(project_data)
    def save_project_to_db(self, project_data: dict):
        """
        Saves the gathered project data to the MongoDB database.
        :param project_data: The project data to be saved.
        """
        self.projects_mongo_collection.insert_one(project_data)

    def get_path_from_home(self, directory: str) -> str:
        """
        Calculates the relative path from the user's home directory.
        :param directory: The directory for which to calculate the path.
        :return: The relative path from the home directory.
        """
        home_directory = os.path.expanduser("~")
        return os.path.relpath(directory, home_directory)

    def gather_project_data(self, directory: str, command: str) -> dict:
        """
        Gathers project data, first analyzing files, then using that information to analyze directories.
        """
        project_name = self.get_project_name(directory)
        subdirectories = self.find_immediate_subdirectories(directory)
        
        # First, analyze files in the root directory
        root_files = self.find_files(directory)
        root_files_metadata = self.gather_metadata_for_files(root_files, command)
        
        # Then analyze each subdirectory with its files
        directories_metadata = self.gather_metadata_for_subdirectories_with_files(subdirectories, command)
        
        path_from_home = self.get_path_from_home(directory)

        return {
            "name": project_name,
            "rootFiles": root_files_metadata,
            "directories": directories_metadata,
            "pathFromHome": path_from_home
        }
    



    
    def find_immediate_subdirectories(self, directory: str) -> list:
        """
        Finds immediate subdirectories within the given directory (only top-level).
        :param directory: The path to the directory to search for subdirectories.
        :return: A list of immediate subdirectories.
        """
        subdirectories = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir():
                    subdirectories.append(os.path.join(directory, entry.name))
        return subdirectories
    
    def find_files(self, directory: str) -> list:
        """
        Finds all files within the given directory (non-recursive).
        :param directory: The directory to scan for files.
        :return: A list of file paths.
        """
        files = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    files.append(os.path.join(directory, entry.name))
        return files
    def get_project_name(self, directory: str) -> str:
        """
        Extracts the project name from the directory.
        :param directory: The root directory of the project.
        :return: The project name.
        """
        return os.path.basename(directory)
    def should_scan_subdirectory(self, subdirectory: str) -> bool:
        from ask_gpt import simple_ask_gpt
        """
        Determines if a subdirectory is important enough to scan by checking if it is necessary for the app to run.
        Uses predefined rules and GPT prompts if necessary.
        :param subdirectory: The path of the subdirectory being analyzed.
        :return: True if it should be scanned, False otherwise.
        """
        # Predefined exclusions
        exclusions = ["node_modules", "__pycache__", ".git", ".vscode", "venv"]

        if os.path.basename(subdirectory) in exclusions:
            return False

        # Optionally ask GPT whether this subdirectory should be scanned
        prompt = f"Should the subdirectory '{os.path.basename(subdirectory)}' in a software project be scanned to understand how the app runs? Answer with Yes or No."
        gpt_response = simple_ask_gpt(prompt)

        return "yes" in gpt_response.lower()

    def gather_metadata_for_subdirectories_with_files(self, subdirectories: list, command: str) -> dict:
        """
        Gathers metadata for subdirectories, incorporating file analysis results.
        """
        directories_metadata = {}

        for subdirectory in subdirectories:
            if self.should_scan_subdirectory(subdirectory):
                # First, analyze all files in the subdirectory
                files = self.find_files(subdirectory)
                files_metadata = self.gather_metadata_for_files(files, command)
                
                # Then use the files metadata to generate a comprehensive directory summary
                directory_summary = self.generate_directory_summary(
                    subdirectory,
                    files_metadata,
                    command
                )
                
                directories_metadata[os.path.basename(subdirectory)] = {
                    "summary": directory_summary,
                    "files": files_metadata
                }

        return directories_metadata

    def generate_directory_summary(self, directory: str, files_metadata: dict, command: str) -> str:
        """
        Generates a summary of the directory's purpose using the analyzed file metadata.
        """
        from ask_gpt import simple_ask_gpt
        
        # Create a summary of the files and their purposes
        files_summary = "\n".join([
            f"- {filename}: {metadata}"
            for filename, metadata in files_metadata.items()
        ])
        
        prompt = f"""Based on the following analysis of files in the directory '{os.path.basename(directory)}',
        provide a comprehensive summary of this directory's purpose and role in the project.
        Use this context about the project: {command}

        Files analysis:
        {files_summary}

        Please describe:
        1. The main purpose of this directory
        2. How it relates to the overall project
        3. Key functionality or features implemented here
        """

        return simple_ask_gpt(prompt)
    
    def should_scan_file(self, file: str) -> bool:
        """
        Determines if a file is important enough to scan.
        """
        from ask_gpt import simple_ask_gpt
        # Predefined exclusions
        exclusions = ["README.md", "LICENSE", ".gitignore"]

        if os.path.basename(file) in exclusions:
            return False

        # Optionally ask GPT whether this file should be scanned
        prompt = f"Should the file '{os.path.basename(file)}' in a software project be scanned to understand how the app runs? Answer with Yes or No."
        gpt_response = simple_ask_gpt(prompt)

        return "yes" in gpt_response.lower()
    

    def gather_metadata_for_files(self, files: list, command: str) -> dict:
        """
        Gathers metadata for files, focusing on their role in the project.
        """
        meta_data = {}

        for file in files:
            if self.should_scan_file(file):
                meta_data[os.path.basename(file)] = self.analyze_file_content(file, command)

        return meta_data

    def analyze_file_content(self, file: str, command: str) -> str:
        """
        Analyzes the content of a file to understand its purpose and functionality.
        """
        from ask_gpt import simple_ask_gpt
        
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # For large files, take a smart sample
            content_preview = self.get_smart_content_preview(content)
            
            prompt = f"""Analyze this file '{os.path.basename(file)}' in the context of {command}.
            Content preview:
            {content_preview}
            
            Provide a concise summary of:
            1. The file's main purpose
            2. Key functionality it implements
            3. How it contributes to the project
            """

            return simple_ask_gpt(prompt)
            
        except Exception as e:
            return f"Could not analyze file: {str(e)}"

    def get_smart_content_preview(self, content: str, max_length: int = 1000) -> str:
        """
        Creates a smart preview of file content, prioritizing important parts.
        """
        if len(content) <= max_length:
            return content
            
        # Take the first part (usually contains imports and important declarations)
        first_part = content[:max_length//3]
        
        # Take a middle part (usually contains main logic)
        middle_start = len(content)//2 - max_length//3//2
        middle_part = content[middle_start:middle_start + max_length//3]
        
        # Take the end part (usually contains important functions or closing logic)
        last_part = content[-max_length//3:]
        
        return f"{first_part}\n...[content trimmed]...\n{middle_part}\n...[content trimmed]...\n{last_part}"



# import os

# class ProjectScanner:
#     projects_mongo_collection = None

#     def __init__(self):
#         from system import get_db
#         db = get_db()
#         self.projects_mongo_collection = db['projects']

#     def scan_project(self, project_directory: str, command: str):
#         """
#         Scans the project directory and creates a project instance in MongoDB.
#         """
#         project_data = self.gather_project_data(project_directory, command)
#         print(project_data)
#         # self.save_project_to_db(project_data)

#     def gather_project_data(self, directory: str, command: str) -> dict:
#         """
#         Gathers project data, including name, directories, metadata, and path.
#         :param directory: The root directory of the project.
#         :param command: Contextual command to pass to GPT for more specific results.
#         :return: A dictionary containing the project data.
#         """
#         project_name = self.get_project_name(directory)
#         subdirectories = self.find_immediate_subdirectories(directory)
#         meta_data = self.gather_metadata_for_subdirectories(subdirectories, command)
#         path_from_home = self.get_path_from_home(directory)

#         return {
#             "name": project_name,
#             "directories": subdirectories,
#             "metaData": meta_data,
#             "pathFromHome": path_from_home
#         }

#     def get_project_name(self, directory: str) -> str:
#         """
#         Extracts the project name from the directory.
#         :param directory: The root directory of the project.
#         :return: The project name.
#         """
#         return os.path.basename(directory)
#     def find_files(self, directory: str) -> list:
#         """
#         Finds all files within the given directory (non-recursive).
#         """
#         files = []
#         with os.scandir(directory) as entries:
#             for entry in entries:
#                 if entry.is_file():
#                     files.append(os.path.join(directory, entry.name))
#         return files

#     def find_immediate_subdirectories(self, directory: str) -> list:
#         """
#         Finds immediate subdirectories within the given directory (only top-level).
#         :param directory: The path to the directory to search for subdirectories.
#         :return: A list of immediate subdirectories.
#         """
#         subdirectories = []
#         with os.scandir(directory) as entries:
#             for entry in entries:
#                 if entry.is_dir():
#                     subdirectories.append(os.path.join(directory, entry.name))
#         return subdirectories

#     def gather_metadata_for_subdirectories(self, subdirectories: list, command: str) -> dict:
#         """
#         Gathers metadata for the immediate subdirectories of a project.
#         Uses GPT to determine if a subdirectory is important and should be scanned, then generates meaningful descriptions for each important subdirectory.
#         :param subdirectories: A list of subdirectory paths.
#         :param command: Contextual command to pass to GPT for more specific results.
#         :return: A dictionary containing metadata for each relevant subdirectory.
#         """
#         meta_data = {}

#         for subdirectory in subdirectories:
#             if self.should_scan_subdirectory(subdirectory):
#                 # Generate metadata only for important subdirectories
#                 gpt_response = self.generate_gpt_metadata_for_subdirectory(subdirectory, command)
#                 meta_data[os.path.basename(subdirectory)] = gpt_response

#         return meta_data
    
#     def gather_metadata_for_files(self, files: list, command: str) -> dict:
#         """
#         Gathers metadata for the immediate files in the project directory.
#         """
#         meta_data = {}

#         for file in files:
#             if self.should_scan_file(file):
#                 gpt_response = self.generate_gpt_metadata_for_file(file, command)
#                 meta_data[os.path.basename(file)] = gpt_response

#         return meta_data

#     def should_scan_subdirectory(self, subdirectory: str) -> bool:
#         from ask_gpt import simple_ask_gpt
#         """
#         Determines if a subdirectory is important enough to scan by checking if it is necessary for the app to run.
#         Uses predefined rules and GPT prompts if necessary.
#         :param subdirectory: The path of the subdirectory being analyzed.
#         :return: True if it should be scanned, False otherwise.
#         """
#         # Predefined exclusions
#         exclusions = ["node_modules", "__pycache__", ".git", ".vscode", "venv"]

#         if os.path.basename(subdirectory) in exclusions:
#             return False

#         # Optionally ask GPT whether this subdirectory should be scanned
#         prompt = f"Should the subdirectory '{os.path.basename(subdirectory)}' in a software project be scanned to understand how the app runs? Answer with Yes or No."
#         gpt_response = simple_ask_gpt(prompt)

#         return "yes" in gpt_response.lower()

#     def generate_gpt_metadata_for_subdirectory(self, subdirectory: str, command: str) -> str:
#         from ask_gpt import simple_ask_gpt
#         """
#         Uses the simple_ask_gpt function to generate meaningful metadata for a subdirectory.
#         :param subdirectory: The path of the subdirectory being analyzed.
#         :param command: Contextual command to guide GPT's response.
#         :return: A GPT-generated description of the subdirectory's purpose and contents.
#         """
#         files_in_subdirectory = self.find_files(subdirectory)
#         file_list = "\n".join([os.path.basename(file) for file in files_in_subdirectory])

#         prompt = (
#             f"Using {command} as context for the project, describe the purpose and contents of "
#             f"the subdirectory '{os.path.basename(subdirectory)}'. "
#             f"Here are the files in this subdirectory:\n{file_list}\n"
#             f"Please focus on whether this subdirectory is core to the project."
#         )

#         gpt_response = simple_ask_gpt(prompt)
#         return gpt_response

#     def find_files(self, directory: str) -> list:
#         """
#         Finds all files within the given directory (non-recursive).
#         :param directory: The directory to scan for files.
#         :return: A list of file paths.
#         """
#         files = []
#         with os.scandir(directory) as entries:
#             for entry in entries:
#                 if entry.is_file():
#                     files.append(os.path.join(directory, entry.name))
#         return files

#     def get_path_from_home(self, directory: str) -> str:
#         """
#         Calculates the relative path from the user's home directory.
#         :param directory: The directory for which to calculate the path.
#         :return: The relative path from the home directory.
#         """
#         home_directory = os.path.expanduser("~")
#         return os.path.relpath(directory, home_directory)

#     def save_project_to_db(self, project_data: dict):
#         """
#         Saves the gathered project data to the MongoDB database.
#         :param project_data: The project data to be saved.
#         """
#         self.projects_mongo_collection.insert_one(project_data)
#     def should_scan_file(self, file: str) -> bool:
#         """
#         Determines if a file is important enough to scan.
#         """
#         # Predefined exclusions
#         exclusions = ["README.md", "LICENSE", ".gitignore"]

#         if os.path.basename(file) in exclusions:
#             return False

#         # Optionally ask GPT whether this file should be scanned
#         prompt = f"Should the file '{os.path.basename(file)}' in a software project be scanned to understand how the app runs? Answer with Yes or No."
#         gpt_response = self.simple_ask_gpt(prompt)

#         return "yes" in gpt_response.lower()
#     def generate_gpt_metadata_for_file(self, file: str, command: str) -> str:
#         """
#         Uses the simple_ask_gpt function to generate meaningful metadata for a file.
#         """
#         try:
#             with open(file, 'r', encoding='utf-8', errors='ignore') as f:
#                 content_preview = f.read(500)  # Read first 500 characters
#         except Exception as e:
#             content_preview = "Could not read file content."

#         prompt = (
#             f"Using '{command}' as context for the project, provide a brief summary of "
#             f"the file '{os.path.basename(file)}'. "
#             f"Here is a preview of its contents:\n{content_preview}\n"
#             f"Please focus on how this file contributes to the project's functionality."
#         )

#         gpt_response = self.simple_ask_gpt(prompt)
#         return gpt_response

# # Example usage:
# # scanner = ProjectScanner()
# # scanner.scan_project("/path/to/your/project", "build an e-commerce app")
