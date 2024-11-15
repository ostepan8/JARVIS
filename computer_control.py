import subprocess
import webbrowser
from ask_gpt import classify_intent, simple_ask_gpt
import subprocess
import platform


def open_desktop_app(app_name):
    system = platform.system()
    
    try:
        if system == "Linux":
            # Open Linux app by command name (app_name must be the command to open the app)
            subprocess.Popen([app_name])
        
        elif system == "Darwin":  # macOS
            # Use 'open' to open macOS apps by their name
            subprocess.Popen(["open", "-a", app_name])  # Opens the specified application
        
        elif system == "Windows":
            # Use 'start' to open Windows applications by their name
            subprocess.Popen(f"start {app_name}", shell=True)
        
        else:
            print(f"Unsupported operating system: {system}")
    
    except FileNotFoundError:
        print(f"Unable to open {app_name}. It may not be installed or available on this system.")


def open_terminal():
    system = platform.system()
    
    try:
        if system == "Linux":
            # For GNOME or any system with gnome-terminal
            subprocess.Popen(["gnome-terminal"])
        elif system == "Darwin":  # macOS
            # Use AppleScript to open a new Terminal window
            subprocess.Popen(["osascript", "-e", 
                              'tell application "Terminal" to do script ""'])
        elif system == "Windows":
            subprocess.Popen("start cmd", shell=True)  # Opens a new Command Prompt window
        else:
            print(f"Unsupported operating system: {system}")
    except FileNotFoundError:
        print("Unable to open terminal.")



def handle_computer_control_input(user_input):
    categories = ['desktop_app', 'website', 'terminal', 'other']
    context_message = "Classify this input strictly as 'desktop_app', 'website', 'terminal', or 'other'. Do not return anything else."
    
    # Classify the user input
    intent = classify_intent(user_input, categories, context_message)
    print(intent, "INTENT")
    
    if intent == 'website':
        # Ask GPT for the exact web link
        link = simple_ask_gpt(f"Return only the exact URL link for {user_input}. Do not return any explanation or extra text. Only the link.")
        link = link.strip()  # Clean up any unwanted spaces
        print(link)
        
        if link.startswith("http"):  # Ensure that the response is a valid URL
            webbrowser.open(link)
        else:
            print(f"Unable to find a valid link for {user_input}.")
    
    elif intent == 'desktop_app':
        # Ask GPT to get the exact name of the desktop application
        app_name = simple_ask_gpt(f"Return only the exact name of the desktop app to open for {user_input}. Do not return any extra information.")
        open_desktop_app(app_name)
    
    elif intent == 'terminal':
        open_terminal()
    
    else:
        print(f"Sorry, I don't know how to handle {user_input}.")
