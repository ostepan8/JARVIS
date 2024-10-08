import os
from system import openai_client


def handle_file_system(userSaid: str):
    # Ensure this module is correctly implemented and accessible
    from ask_gpt import classify_intent
    """
    Main function to handle file system operations based on user input.
    """
    # Define possible intents
    intents = ["Add File", "Remove File", "Add Directory",
               "Remove Directory", "Get Directory"]

    # Classify the intent from the user input
    intent = classify_intent(userSaid, intents)

    if intent in intents:
        chosen_directory = handle_file_system(
            userSaid, intent=intent)

        if chosen_directory:
            # Call the respective function based on the intent
            perform_action(intent, chosen_directory, userSaid)
        else:
            print("No valid directory was chosen.")
    else:
        print("Intent not recognized. Please try again.")


def handle_file_system(userSaid: str, current_directory=os.path.expanduser("~"), relative_path: str = "", intent: str = "") -> str:
    """
    Recursively scans directories and prompts ChatGPT to choose an action.
    Returns the path of the chosen directory where the action should be performed.
    """
    print(f"Scanning directory: {current_directory}")

    # Get the list of directories in the current directory
    try:
        directories = [d for d in os.listdir(current_directory) if os.path.isdir(
            os.path.join(current_directory, d))]
    except PermissionError:
        print(
            f"Permission denied: Cannot access directory '{current_directory}'.")
        return None
    except FileNotFoundError:
        print(f"Directory '{current_directory}' does not exist.")
        return None

    # If there are no directories, return the current path as the chosen directory
    if not directories:
        print("No more subdirectories to explore.")
        return current_directory
    print(directories)
    print(current_directory, "curr")
    # Prompt ChatGPT to pick a directory or suggest an action based on the intent
    action = prompt_chatgpt_for_directory(
        userSaid, current_directory, directories, intent)
    if (action == "Get Directory"):
        return current_directory

    # Extract target directory if mentioned
    target_directory = extract_target_directory(userSaid, directories)

    if target_directory:
        # If a target directory is specified, navigate into it
        action = target_directory

    if action in directories:
        # If ChatGPT picked a directory, recursively scan that directory
        next_directory_path = os.path.join(current_directory, action)
        return handle_file_system(userSaid, next_directory_path, relative_path, intent=intent)
    elif action in ["Add File", "Remove File", "Add Directory", "Remove Directory"]:
        # If ChatGPT picked an action, perform it on the current directory
        return current_directory
    else:
        print("No valid action or directory picked by ChatGPT.")
        return None


def perform_action(intent: str, chosen_directory: str, userSaid: str):
    """
    Executes the desired action (add/remove file or directory) in the chosen directory.
    """
    name = get_name(userSaid=userSaid)

    if name:
        if intent == "Add File":
            # Add a file in the chosen directory
            add_file(os.path.join(chosen_directory, name))
        elif intent == "Remove File":
            # Remove a file in the chosen directory
            remove_file(os.path.join(chosen_directory, name))
        elif intent == "Add Directory":
            # Add a new directory in the chosen directory
            add_directory(os.path.join(chosen_directory, name))
        elif intent == "Remove Directory":
            # Remove a directory in the chosen directory
            remove_directory(os.path.join(chosen_directory, name))
        else:
            print("No valid action was determined.")
    else:
        print("No valid name provided. Action cannot be performed.")


def get_name(userSaid: str) -> str:
    """
    Uses ChatGPT to extract the name of the file or directory from the user's input.
    Reprompts the user if extraction fails.
    """
    while True:
        # Create a message for ChatGPT with strict instructions
        messages = [
            {"role": "system", "content": (
                "You are an assistant that helps with file management tasks. "
                "Your goal is to extract the exact name of the file or directory mentioned in the user's input. "
                "Respond with only the exact name, or 'None' if the name is not clear. Do not provide any additional text."
            )},
            {"role": "user", "content": f"The user wants to manage a file or directory with the following input: '{userSaid}'"},
            {"role": "user", "content": (
                "Please extract and respond with the exact name and capitalization of the file or directory. "
                "If the name is not clear, respond with 'None'."
            )}
        ]

        try:
            # Get the response from ChatGPT
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            # Extract the suggested name from the response
            extracted_name = completion.choices[0].message.content.strip()
            print(f"ChatGPT determined the name: {extracted_name}")

            # Check if ChatGPT provided a valid name
            if is_valid_name(extracted_name):
                return extracted_name
            elif extracted_name.lower() == "none":
                # Reprompt the user for the name
                user_input = input(
                    "ChatGPT couldn't determine the name. Please enter the name of the file or directory: ").strip()
                if is_valid_name(user_input):
                    return user_input
                else:
                    print("Invalid name entered. Please try again.")
            else:
                # If ChatGPT provided an invalid response, treat it as 'None' and reprompt
                user_input = input(
                    "ChatGPT couldn't determine the name. Please enter the name of the file or directory: ").strip()
                if is_valid_name(user_input):
                    return user_input
                else:
                    print("Invalid name entered. Please try again.")
        except Exception as e:
            print(f"An error occurred while communicating with ChatGPT: {e}")
            user_input = input(
                "Please enter the name of the file or directory: ").strip()
            if is_valid_name(user_input):
                return user_input
            else:
                print("Invalid name entered. Please try again.")


def is_valid_name(name: str) -> bool:
    """
    Validates the provided name to ensure it doesn't contain prohibited characters and is not empty.
    """
    # Define prohibited characters for filenames and directory names
    # Characters not allowed in filenames
    prohibited_chars = set('/\\?%*:|"<>')
    if not name:
        return False
    if any(char in prohibited_chars for char in name):
        return False
    return True


def extract_target_directory(userSaid: str, directories: list) -> str:
    """
    Extracts the target directory name from the user's command if mentioned.
    Returns the directory name if found in the available directories; otherwise, returns None.
    """
    userSaid_lower = userSaid.lower()
    for directory in directories:
        if directory.lower() in userSaid_lower:
            return directory
    return None


def prompt_chatgpt_for_directory(userSaid: str, current_directory: str, directories: list, intent: str) -> str:
    """
    Prompts ChatGPT to select a subdirectory or suggest an action based on the user's intent.
    """
    # Define valid choices
    valid_choices = directories + \
        ["Add File", "Remove File", "Add Directory",
            "Remove Directory", "Get Directory"]

    # Extract the last part of the current directory path (i.e., the directory name after the final slash)
    current_directory_name = current_directory.rstrip('/').split('/')[-1]

    # Use the extract_target_directory function to see if the current directory name is mentioned in user input
    target_directory = extract_target_directory(userSaid, directories)
    potentially_desired_directory = (
        current_directory_name == target_directory)

   # Create a concise instruction message for ChatGPT
    system_message = (
        "You help with file management tasks. Respond with one of: "
        f"{', '.join(directories)}, 'Add File', 'Remove File', 'Add Directory', 'Get Directory', or 'Remove Directory'. "
        f"'Get Directory' should only be returned if the current path '{current_directory}' is the desired directory. "
        "Do not return 'Get Directory' if a subdirectory is the target."
    )

    # Assemble the messages with clearer instructions
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"User's intent: '{userSaid}'."},
        {"role": "user", "content": (
            f"Current path: '{current_directory}', subdirectories: {', '.join(directories)}."
        )},
        {"role": "user", "content": (
            f"If the current path '{current_directory}' is the desired directory, respond with 'Get Directory'. "
            "Otherwise, respond with a subdirectory name or choose an action: 'Add File', 'Remove File', 'Add Directory', or 'Remove Directory'."
        )},
    ]

    # Add a specific message if the current directory is flagged as the potential target
    if potentially_desired_directory:
        messages.append({
            "role": "user",
            "content": (
                f"The current path '{current_directory}' is flagged as the potential target since it matches the last part of '{target_directory}'. "
                "Prioritize returning 'Get Directory' if this is correct."
            )
        })

    try:
        # Get the decision from ChatGPT
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        # Extract the suggested action from the response
        suggested_action = completion.choices[0].message.content.strip()

        # Ensure the response is strictly one of the valid choices
        if suggested_action in valid_choices:
            return suggested_action
        else:
            print("Invalid response received from ChatGPT. Please try again or ensure ChatGPT is responding correctly.")
            return None
    except Exception as e:
        print(f"An error occurred while communicating with ChatGPT: {e}")
        return None


def add_file(file_path: str):
    """
    Creates a new file at the specified path.
    """
    try:
        with open(file_path, 'w') as file:
            file.write('')  # Create an empty file
        print(f"File '{file_path}' created successfully.")
    except PermissionError:
        print(f"Permission denied: Cannot create file '{file_path}'.")
    except Exception as e:
        print(f"Failed to create file '{file_path}'. Error: {e}")


def remove_file(file_path: str):
    """
    Removes a file at the specified path.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' removed successfully.")
        else:
            print(f"File '{file_path}' does not exist.")
    except PermissionError:
        print(f"Permission denied: Cannot remove file '{file_path}'.")
    except Exception as e:
        print(f"Failed to remove file '{file_path}'. Error: {e}")


def add_directory(dir_path: str):
    """
    Creates a new directory at the specified path.
    """
    try:
        os.makedirs(dir_path)
        print(f"Directory '{dir_path}' created successfully.")
    except PermissionError:
        print(f"Permission denied: Cannot create directory '{dir_path}'.")
    except Exception as e:
        print(f"Failed to create directory '{dir_path}'. Error: {e}")


def remove_directory(dir_path: str):
    """
    Removes a directory at the specified path.
    """
    try:
        if os.path.exists(dir_path):
            os.rmdir(dir_path)
            print(f"Directory '{dir_path}' removed successfully.")
        else:
            print(f"Directory '{dir_path}' does not exist.")
    except PermissionError:
        print(f"Permission denied: Cannot remove directory '{dir_path}'.")
    except OSError:
        print(f"Directory '{dir_path}' is not empty or cannot be removed.")
    except Exception as e:
        print(f"Failed to remove directory '{dir_path}'. Error: {e}")
