from dotenv import load_dotenv
import os
import requests
from system import openai_client

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Roku IP address from the environment variables
ROKU_IP_ADDRESS = os.getenv('ROKU_IP_ADDRESS')

def get_tv_command_intent(text):
    """
    Classifies the given text to determine the specific Roku TV command.

    Args:
        text (str): The text input to classify.

    Returns:
        str: The determined command intent for controlling the Roku TV.
    """
    # List of Roku TV command categories
    tv_commands = [
        'Power TV on',
        'Power TV off',
        'Launch app',
        'Control playback',
        'Adjust volume',
        'Change channel',
        'Select input',
        'Toggle power',
        'Navigate',
        'Back',
        'Home',
        'Info',
        'Instant Replay',
        'Set sleep timer',
        'Set closed captioning',
        'Set volume',
        'Find remote',
        'Volume up',
        'Volume down',
        'Open Hulu',
        'Open Peacock',
        'Other'
    ]

    # Create a system message to classify the command
    messages = [
        {
            "role": "system",
            "content": (
                "You are an intelligent assistant. Your task is to classify the following sentence into exactly one of these Roku TV commands: "
                + ", ".join(f"'{command}'" for command in tv_commands) + ". "
                "You must return only one command from this list, exactly as it is written. Do not add, remove, or change any words. "
                "For example, 'Turn TV on' and 'Adjust volume' are valid submissions. 'Turn the TV on' is not a valid submission. "
                "Your response must be one of the commands from the list above and nothing else. Do not provide any explanations, interpretations, or variations—just output the exact command."
            )
        },
        {"role": "user", "content": text}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=messages,
        max_tokens=10,  # Limit to a small number to enforce brevity
        temperature=0.0  # Lower temperature to reduce randomness
    )

    # Correctly access the content of the response
    command_intent = response.choices[0].message.content.strip().lower()  # Normalize to lowercase
    return command_intent


def handle_tv_command(main_intent):
    """
    Executes the appropriate function based on the given TV command intent.

    Args:
        command_intent (str): The determined command intent for controlling the Roku TV.

    Returns:
        None
    """
    command_intent = get_tv_command_intent(main_intent)
    # Normalize the command intent to lowercase to avoid case inconsistencies
    command_intent = command_intent.lower()
    
    if command_intent == 'power tv on':
        turn_on_tv()
    elif command_intent == 'power tv off':
        power_off_tv()
    elif command_intent == 'launch app':
        # Example: Replace '12' with the desired app ID or obtain dynamically
        app_id = '12'
        launch_app(app_id)
    elif command_intent == 'control playback':
        # Example: Replace 'play' with the actual playback action parsed from text
        playback_action = 'play'
        control_playback(playback_action)
    elif command_intent == 'adjust volume':
        # Example: Replace 'volumeup' with the actual volume action parsed from text
        volume_action = 'volumeup'
        adjust_volume(volume_action)
    elif command_intent == 'change channel':
        # Example: Replace '5' with the actual channel number parsed from text
        channel_number = '5'
        change_channel(channel_number)
    elif command_intent == 'select input':
        # Example: Replace 'HDMI1' with the actual input parsed from text
        input_name = 'HDMI1'
        select_input(input_name)
    elif command_intent == 'toggle power':
        toggle_power()
    elif command_intent == 'navigate':
        # Example: Replace 'up' with the actual navigation direction parsed from text
        direction = 'up'
        navigate(direction)
    elif command_intent == 'back':
        back()
    elif command_intent == 'home':
        home()
    elif command_intent == 'info':
        info()
    elif command_intent == 'instant replay':
        instant_replay()
    elif command_intent == 'set sleep timer':
        # Example: Replace '30' with the actual number of minutes parsed from text
        minutes = 30
        sleep_timer(minutes)
    elif command_intent == 'set closed captioning':
        # Example: Replace 'On' with the actual captioning state parsed from text
        state = 'On'
        set_closed_captioning(state)
    elif command_intent == 'set volume':
        # Example: Replace '10' with the actual volume level parsed from text
        volume_level = 10
        volume(volume_level)
    elif command_intent == 'find remote':
        find_remote()
    elif command_intent == 'volume up':
        volume_up()
    elif command_intent == 'volume down':
        volume_down()
    elif command_intent == 'open hulu':
        open_hulu()
    elif command_intent == 'open peacock':
        open_peacock()
    else:
        print("Unknown command. Please try again.")


def send_roku_command(endpoint):
    """
    Sends a command to the Roku TV using the specified endpoint.
    
    Args:
        endpoint (str): The Roku API endpoint to send the command to.
        
    Returns:
        None
    """
    if not ROKU_IP_ADDRESS:
        print("Roku IP address not found. Please check your .env file.")
        return

    url = f'http://{ROKU_IP_ADDRESS}:8060/{endpoint}'
    try:
        response = requests.post(url)
        if response.status_code == 200:
            print(f'Successfully sent command to {endpoint}')
        else:
            print(f'Failed to send command. Status code: {response.status_code}')
    except requests.RequestException as e:
        print(f'Error sending command to Roku: {e}')


def turn_on_tv():
    """
    Attempts to turn on the Roku TV by sending multiple key press commands.
    """
    send_roku_command('keypress/poweron')  # Try using 'poweron' if supported


def volume_up():
    """
    Increases the volume on the Roku TV by 5 steps.
    """
    for _ in range(5):
        send_roku_command('keypress/volumeup')


def volume_down():
    """
    Decreases the volume on the Roku TV by 5 steps.
    """
    for _ in range(5):
        send_roku_command('keypress/volumedown')


def launch_app(app_id):
    """
    Launches a specific app on the Roku TV.
    
    Args:
        app_id (str): The ID of the app to launch.
    """
    send_roku_command(f'launch/{app_id}')


def open_hulu():
    """
    Opens the Hulu app on the Roku TV.
    """
    hulu_app_id = '2285'  # Hulu app ID on Roku
    launch_app(hulu_app_id)


def open_peacock():
    """
    Opens the Peacock app on the Roku TV.
    """
    peacock_app_id = '61322'  # Peacock app ID on Roku
    launch_app(peacock_app_id)


def control_playback(action):
    """
    Controls playback on the Roku TV (play, pause, fast-forward, rewind).
    
    Args:
        action (str): The playback action ('play', 'pause', 'fastforward', 'rewind').
    """
    if action in ['play', 'pause', 'fastforward', 'rewind']:
        send_roku_command(f'keypress/{action}')


def navigate(direction):
    """
    Navigates the Roku TV interface (up, down, left, right, select).
    
    Args:
        direction (str): The direction to navigate ('up', 'down', 'left', 'right', 'select').
    """
    if direction in ['up', 'down', 'left', 'right', 'select']:
        send_roku_command(f'keypress/{direction}')


def adjust_volume(action):
    """
    Adjusts the volume on the Roku TV (volume up, volume down, mute).
    
    Args:
        action (str): The volume action ('volumeup', 'volumedown', 'mute').
    """
    if action in ['volumeup', 'volumedown', 'mute']:
        send_roku_command(f'keypress/{action}')


def change_channel(channel_number):
    """
    Changes the channel on the Roku TV to the specified channel number.
    
    Args:
        channel_number (str): The number of the channel to change to.
    """
    send_roku_command(f'tv/tune?channel={channel_number}')


def select_input(input_name):
    """
    Selects a specific input on the Roku TV (e.g., HDMI1, HDMI2).
    
    Args:
        input_name (str): The name of the input to select (e.g., 'HDMI1', 'HDMI2').
    """
    send_roku_command(f'keypress/Input{input_name}')


def toggle_power():
    """
    Toggles the power of the Roku TV (on/off).
    """
    send_roku_command('keypress/Power')


def back():
    """
    Sends the 'Back' command to return to the previous screen.
    """
    send_roku_command('keypress/Back')


def home():
    """
    Sends the 'Home' command to return to the Roku home screen.
    """
    send_roku_command('keypress/home')


def info():
    """
    Sends the 'Info' command to display information about the current program or app.
    """
    send_roku_command('keypress/Info')


def instant_replay():
    """
    Sends the 'Instant Replay' command to replay the last few seconds of the current program.
    """
    send_roku_command('keypress/InstantReplay')


def sleep_timer(minutes):
    """
    Sets a sleep timer on the Roku TV.
    
    Args:
        minutes (int): Number of minutes after which the TV should turn off.
    """
    send_roku_command(f'keypress/SleepTimer{minutes}')


def set_closed_captioning(state):
    """
    Sets the closed captioning state on the Roku TV.
    
    Args:
        state (str): The state of the closed captioning ('On', 'Off', 'OnMute').
    """
    if state in ['On', 'Off', 'OnMute']:
        send_roku_command(f'keypress/ClosedCaption{state}')


def volume(level):
    """
    Sets the volume on the Roku TV to a specific level.
    
    Args:
        level (int): Volume level (usually between 0 and 100).
    """
    for _ in range(level):
        send_roku_command('keypress/volumeup')


def find_remote():
    """
    Sends a command to the Roku TV to play a sound on the remote for locating it.
    """
    send_roku_command('keypress/FindRemote')



def power_off_tv():
    """
    Powers off the Roku TV.
    """
    send_roku_command('keypress/PowerOff')
