import os
import requests
from dotenv import load_dotenv
from system import openai_client
import time
# Load environment variables from the .env file
load_dotenv()

# Retrieve the Roku IP address from the environment variables
ROKU_IP_ADDRESS = os.getenv('ROKU_IP_ADDRESS')


# Load environment variables from the .env file
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_API_URL = "https://api.themoviedb.org/3"
TMDB_PROVIDER_REGION = "US"  # Change to your region code if necessary

TMDB_PROVIDER_MAPPING = {
    'Netflix': {'provider_id': 8, 'roku_app_name': 'Netflix'},
    'Hulu': {'provider_id': 15, 'roku_app_name': 'Hulu'},
    'Amazon Prime Video': {'provider_id': 9, 'roku_app_name': 'Prime Video'},
    'Disney Plus': {'provider_id': 337, 'roku_app_name': 'Disney Plus'},
    'HBO Max': {'provider_id': 384, 'roku_app_name': 'HBO Max'},
    # Add more providers as needed
}


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
        'Open app',
        'Play TV Show',
        'Play Movie',  
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
                "Your response must be one of the commands from the list above and nothing else. Do not provide any explanations, interpretations, or variations—just output the exact command."
            )
        },
        {"role": "user", "content": text}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=10,
        temperature=0.0
    )

    command_intent = response.choices[0].message.content.strip()
    print(command_intent, "TV_INTENT")
    return command_intent

def play_tv_show(tv_show_name):
    """
    Attempts to play a TV show by determining the streaming service and launching the app.

    Args:
        tv_show_name (str): The name of the TV show to play.
    """
    # Step 1: Find out which streaming service has the TV show
    providers = search_tv_show_on_providers(tv_show_name)
    if not providers:
        print(f"Could not find '{tv_show_name}' on available streaming services.")
        return

    # Step 2: Map provider to Roku app
    for provider in providers:
        provider_info = TMDB_PROVIDER_MAPPING.get(provider)
        if provider_info:
            app_name = provider_info['roku_app_name']
            # Launch the app and inform the user
            home()
            launch_app_by_name(app_name)
            print(f"Opened {app_name} for '{tv_show_name}'. Please search for the show in the app.")
            if app_name.lower() == 'hulu':
                # Call the Hulu-specific search and select function
                search_and_select_hulu(tv_show_name)
                return
            

    print(f"Streaming service for '{tv_show_name}' is not supported.")


def play_movie(movie_name):
    """
    Attempts to play a movie by determining the streaming service and launching the app.

    Args:
        movie_name (str): The name of the movie to play.
    """
    # Step 1: Find out which streaming service has the movie
    providers = search_movie_on_providers(movie_name)
    if not providers:
        print(f"Could not find '{movie_name}' on available streaming services.")
        return

    # Step 2: Map provider to Roku app
    for provider in providers:
        provider_info = TMDB_PROVIDER_MAPPING.get(provider)
        if provider_info:
            app_name = provider_info['roku_app_name']
            home()
            launch_app_by_name(app_name)
            print(f"Opened {app_name} for '{movie_name}'. Please search for the show in the app.")
            if app_name.lower() == 'hulu':
                # Call the Hulu-specific search and select function
                search_and_select_hulu(movie_name)
                return

    print(f"Streaming service for '{movie_name}' is not supported.")
def search_movie_on_providers(movie_name):
    """
    Searches for the movie on various streaming providers using TMDb API.

    Args:
        movie_name (str): The name of the movie.

    Returns:
        list: A list of provider names where the movie is available.
    """
    headers = {
        'User-Agent': 'JarvisTV/1.0'
    }
    print("Searching for movie providers...")
    try:
        # Step 1: Search for the movie ID
        search_url = f"{TMDB_API_URL}/search/movie"
        search_params = {
            'api_key': TMDB_API_KEY,
            'query': movie_name,
            'language': 'en-US',
            'page': 1,
        }
        search_response = requests.get(search_url, params=search_params, headers=headers)
        print(search_response)
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(search_data)
            if 'results' in search_data and len(search_data['results']) > 0:
                movie_id = search_data['results'][0]['id']
            else:
                print(f"No results found for '{movie_name}'.")
                return []
        else:
            print(f"TMDb search API error: {search_response.status_code}")
            return []

        # Step 2: Get the providers for the movie
        provider_url = f"{TMDB_API_URL}/movie/{movie_id}/watch/providers"
        provider_params = {
            'api_key': TMDB_API_KEY,
        }
        provider_response = requests.get(provider_url, params=provider_params, headers=headers)

        if provider_response.status_code == 200:
            provider_data = provider_response.json()
            print(provider_data)
            if TMDB_PROVIDER_REGION in provider_data['results']:
                providers_info = provider_data['results'][TMDB_PROVIDER_REGION]
                providers = set()
                for provider_type in ['flatrate', 'ads', 'free', 'rent', 'buy']:
                    if provider_type in providers_info:
                        for provider in providers_info[provider_type]:
                            provider_name = provider['provider_name']
                            if provider_name in TMDB_PROVIDER_MAPPING:
                                providers.add(provider_name)
                return list(providers)
            else:
                print(f"No providers found in region '{TMDB_PROVIDER_REGION}'.")
                return []
        else:
            print(f"TMDb provider API error: {provider_response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error querying TMDb API: {e}")
    return []




def search_tv_show_on_providers(tv_show_name):
    """
    Searches for the TV show on various streaming providers using TMDb API.

    Args:
        tv_show_name (str): The name of the TV show.

    Returns:
        list: A list of provider names where the show is available.
    """
    headers = {
        'User-Agent': 'JarvisTV/1.0'
    }
    try:
        # Step 1: Search for the TV show ID
        search_url = f"{TMDB_API_URL}/search/tv"
        search_params = {
            'api_key': TMDB_API_KEY,
            'query': tv_show_name,
            'language': 'en-US',
            'page': 1,
        }
        search_response = requests.get(search_url, params=search_params, headers=headers)
        print(search_response)
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(search_data)
            if 'results' in search_data and len(search_data['results']) > 0:
                tv_show_id = search_data['results'][0]['id']
            else:
                print(f"No results found for '{tv_show_name}'.")
                return []
        else:
            print(f"TMDb search API error: {search_response.status_code}")
            return []

        # Step 2: Get the providers for the TV show
        provider_url = f"{TMDB_API_URL}/tv/{tv_show_id}/watch/providers"
        provider_params = {
            'api_key': TMDB_API_KEY,
        }
        provider_response = requests.get(provider_url, params=provider_params, headers=headers)

        if provider_response.status_code == 200:
            provider_data = provider_response.json()
            if TMDB_PROVIDER_REGION in provider_data['results']:
                providers_info = provider_data['results'][TMDB_PROVIDER_REGION]
                providers = set()
                for provider_type in ['flatrate', 'ads', 'free', 'rent', 'buy']:
                    if provider_type in providers_info:
                        for provider in providers_info[provider_type]:
                            provider_name = provider['provider_name']
                            if provider_name in TMDB_PROVIDER_MAPPING:
                                providers.add(provider_name)
                return list(providers)
            else:
                print(f"No providers found in region '{TMDB_PROVIDER_REGION}'.")
                return []
        else:
            print(f"TMDb provider API error: {provider_response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error querying TMDb API: {e}")
    return []

def search_and_select_hulu(tv_show_name):
    """
    Navigates to the search bar in the Hulu app on Roku and searches for a TV show.

    Args:
        tv_show_name (str): The name of the TV show to search for.
    """
    time.sleep(7)  # Wait for 7 seconds after launching the Hulu app
    # Navigate to the search option
    send_roku_command('keypress/Select')
    time.sleep(3.5)
    send_roku_command('keypress/Left')
    time.sleep(0.2)
    send_roku_command('keypress/Up')
    time.sleep(0.2)
    send_roku_command('keypress/Select')
    time.sleep(0.2)

    # Convert the input to lowercase to match the position matrix
    tv_show_name = tv_show_name.lower()
    # Calculate the optimal path for typing the TV show name
    path,current_position = calculate_optimal_path(tv_show_name)
    print("Order:", path)

    # Send the Roku commands based on the calculated path
    for command in path:
        time.sleep(0.2)  # Adding a small delay between commands
        send_roku_command(command)
        time.sleep(0.2)
    column_position = current_position[1]
    while column_position < 6:  # Assuming the rightmost column is 5
        send_roku_command('keypress/Right')
        time.sleep(0.2)
        column_position += 1

    # Select the search/submit button
    send_roku_command('keypress/Select')
    time.sleep(1)
    send_roku_command('keypress/Select')


def get_position_matrix():
    # Create a dictionary that maps each character to its (x, y) position
    layout = [
        ['a', 'b', 'c', 'd', 'e', 'f'],
        ['g', 'h', 'i', 'j', 'k', 'l'],
        ['m', 'n', 'o', 'p', 'q', 'r'],
        ['s', 't', 'u', 'v', 'w', 'x'],
        ['y', 'z', '1', '2', '3', '4'],
        ['5', '6', '7', '8', '9', '0'],

    ]
    
    position_matrix = {}
    for i in range(len(layout)):
        for j in range(len(layout[i])):
            position_matrix[layout[i][j]] = (i, j)
    return position_matrix


def calculate_optimal_path(word):
    # Initialize the position of the cursor
    current_position = (0, 0)  # Start at 'a'
    path = []
    position_matrix = get_position_matrix()
    print(position_matrix)

    for char in word:
        if char.lower() not in position_matrix and char != " ":
            continue

        if char == " ":
            # Move vertically to the bottom row
            while current_position[0] < 6:
                path.append('keypress/Down')
                current_position = (current_position[0] + 1, current_position[1])
            # Move horizontally to the first column
            while current_position[1] > 1:
                path.append('keypress/Left')
                current_position = (current_position[0], current_position[1] - 1)
            path.append('keypress/Right')
            current_position = (current_position[0], current_position[1] + 1)
            # Select the "space" key
            path.append('keypress/Select')
            continue

        # Convert character to lowercase to match matrix keys
        char = char.lower()

        target_position = position_matrix[char]
        print(char, target_position, "c->t-p")

        # Calculate the vertical movement
        while current_position[0] < target_position[0]:
            path.append('keypress/Down')
            current_position = (current_position[0] + 1, current_position[1])
        while current_position[0] > target_position[0]:
            path.append('keypress/Up')
            current_position = (current_position[0] - 1, current_position[1])

        # Calculate the horizontal movement
        while current_position[1] < target_position[1]:
            path.append('keypress/Right')
            current_position = (current_position[0], current_position[1] + 1)
        while current_position[1] > target_position[1]:
            path.append('keypress/Left')
            current_position = (current_position[0], current_position[1] - 1)

        # Select the character
        path.append('keypress/Select')

    return path, current_position




def send_roku_command_with_retry(command, retries=10, delay=2.5):
    """
    Sends a command to the Roku device and retries if it fails.

    Args:
        command (str): The command to send to the Roku device.
        retries (int): Number of times to retry if the command fails.
        delay (int): Time in seconds to wait between retries.
    """
    print(command)
    for attempt in range(retries):
        response = send_roku_command(command)
        if response and response.status_code == 200:
            print(f"Successfully sent command: {command}")
            return True
        else:
            print(f"Attempt {attempt + 1} failed, retrying in {delay} seconds...")
            time.sleep(delay)
    print(f"Failed to send command: {command} after {retries} attempts.")
    return False


def extract_tv_show_name(user_input):
    """
    Extracts the TV show or movie name from the user's input and corrects it to the official title.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The corrected TV show or movie name, or None if not found.
    """
    print("User input:", user_input)
    # Step 1: Use ChatGPT to extract the TV show or movie name from the user's input
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts TV show or movie names from user requests. "
                "Extract the exact name of the TV show or movie the user wants to watch from the following input. "
                "Respond with only the TV show or movie name and nothing else. If you cannot find a TV show or movie name, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=20,
        temperature=0.0
    )

    extracted_name = response.choices[0].message.content.strip()
    if extracted_name.lower() == 'none':
        return None

    # Step 2: Use TMDb API to find the correct title
    # Search for the movie or TV show using the extracted name
    import requests

    search_url = f"{TMDB_API_URL}/search/multi"
    search_params = {
        'api_key': TMDB_API_KEY,
        'query': extracted_name,
        'language': 'en-US',
        'page': 1,
        'include_adult': False
    }
    try:
        response = requests.get(search_url, params=search_params)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                # Get the first result's title
                result = data['results'][0]
                media_type = result.get('media_type')
                if media_type == 'tv':
                    corrected_title = result.get('name')
                elif media_type == 'movie':
                    corrected_title = result.get('title')
                else:
                    corrected_title = extracted_name  # Use extracted name if media_type is unknown
                return corrected_title
            else:
                print(f"No results found for '{extracted_name}'.")
                return extracted_name  # Return the extracted name if no results found
        else:
            print(f"TMDb API error: {response.status_code}")
            return extracted_name  # Return the extracted name if API call fails
    except requests.RequestException as e:
        print(f"Error querying TMDb API: {e}")
        return extracted_name  # Return the extracted name if an exception occurs




def handle_tv_command(user_input):
    """
    Executes the appropriate function based on the given TV command intent.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        None
    """
    command_intent = get_tv_command_intent(user_input)
    # Normalize the command intent to lowercase to avoid case inconsistencies
    command_intent_lower = command_intent.lower()
    if command_intent_lower == 'play tv show':
    
        # Use ChatGPT to extract the TV show name
        tv_show_name = extract_tv_show_name(user_input)
        if tv_show_name:
            play_tv_show(tv_show_name)
        else:
            print("Could not determine the TV show to play.")
    elif command_intent_lower == 'play movie':
        
        # Use ChatGPT to extract the TV show name
        movie_name = extract_tv_show_name(user_input)
        if movie_name:
            play_movie(movie_name)
        else:
            print("Could not determine the TV show to play.")
    elif command_intent_lower == 'power tv on':
        turn_on_tv()
    elif command_intent_lower == 'power tv off':
        power_off_tv()
    elif command_intent_lower == 'launch app' or command_intent_lower == 'open app':
        # Use ChatGPT to extract the app name from user input
        app_name = extract_app_name(user_input)
        if app_name:
            launch_app_by_name(app_name)
        else:
            print("Could not determine the app to launch.")
    elif command_intent_lower == 'control playback':
        # Use ChatGPT to extract playback action
        playback_action = extract_playback_action(user_input)
        if playback_action:
            control_playback(playback_action)
        else:
            print("Could not determine the playback action.")
    elif command_intent_lower == 'adjust volume':
        # Use ChatGPT to extract volume adjustment
        volume_change = extract_volume_change(user_input)
        if volume_change != 0:
            adjust_volume(volume_change)
        else:
            print("Could not determine how much to adjust the volume.")
    elif command_intent_lower == 'change channel':
        # Use ChatGPT to extract channel number
        channel_number = extract_channel_number(user_input)
        if channel_number:
            change_channel(channel_number)
        else:
            print("Could not determine the channel number.")
    elif command_intent_lower == 'select input':
        # Use ChatGPT to extract input name
        input_name = extract_input_name(user_input)
        if input_name:
            select_input(input_name)
        else:
            print("Could not determine the input name.")
    elif command_intent_lower == 'toggle power':
        toggle_power()
    elif command_intent_lower == 'navigate':
        # Use ChatGPT to extract navigation direction
        direction = extract_navigation_direction(user_input)
        if direction:
            navigate(direction)
        else:
            print("Could not determine the navigation direction.")
    elif command_intent_lower == 'back':
        back()
    elif command_intent_lower == 'home':
        home()
    elif command_intent_lower == 'info':
        info()
    elif command_intent_lower == 'instant replay':
        instant_replay()
    elif command_intent_lower == 'set sleep timer':
        # Use ChatGPT to extract sleep timer duration
        minutes = extract_sleep_timer_duration(user_input)
        if minutes:
            sleep_timer(minutes)
        else:
            print("Could not determine the sleep timer duration.")
    elif command_intent_lower == 'set closed captioning':
        # Use ChatGPT to extract captioning state
        state = extract_captioning_state(user_input)
        if state:
            set_closed_captioning(state)
        else:
            print("Could not determine the closed captioning state.")
    elif command_intent_lower == 'set volume':
        # Use ChatGPT to extract volume level
        volume_level = extract_volume_level(user_input)
        if volume_level is not None:
            set_volume(volume_level)
        else:
            print("Could not determine the volume level.")
    elif command_intent_lower == 'find remote':
        find_remote()
    elif command_intent_lower == 'volume up':
        volume_up(user_input)
    elif command_intent_lower == 'volume down':
        volume_down(user_input)
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



# Functions for controlling the TV

def turn_on_tv():
    """
    Turns on the Roku TV.
    """
    send_roku_command('keypress/PowerOn')


def power_off_tv():
    """
    Powers off the Roku TV.
    """
    send_roku_command('keypress/PowerOff')


def launch_app_by_name(app_name):
    """
    Launches an app on the Roku TV by its name.

    Args:
        app_name (str): The name of the app to launch.
    """
    app_id = get_app_id_by_name(app_name)
    if app_id:
        launch_app(app_id)
    else:
        print(f"App '{app_name}' not found.")


def get_app_id_by_name(app_name):
    """
    Retrieves the app ID for a given app name.

    Args:
        app_name (str): The name of the app.

    Returns:
        str: The app ID, or None if not found.
    """
    # Fetch the list of installed apps from the Roku device
    url = f'http://{ROKU_IP_ADDRESS}:8060/query/apps'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            from xml.etree import ElementTree
            apps_xml = response.content
            root = ElementTree.fromstring(apps_xml)
            for app in root.findall('app'):
                if app.text.lower() == app_name.lower():
                    return app.attrib['id']
        else:
            print(f"Failed to retrieve app list. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error retrieving app list from Roku: {e}")
    return None


def launch_app(app_id):
    """
    Launches a specific app on the Roku TV.

    Args:
        app_id (str): The ID of the app to launch.
    """
    send_roku_command(f'launch/{app_id}')


def control_playback(action):
    """
    Controls playback on the Roku TV (play, pause, fast-forward, rewind).

    Args:
        action (str): The playback action ('play', 'pause', 'fastforward', 'rewind').
    """
    valid_actions = {
        'play': 'Play',
        'pause': 'Play',  # 'Play' toggles play/pause
        'fast forward': 'Fwd',
        'rewind': 'Rev',
        'stop': 'Stop',
        'forward': 'Fwd',
        'reverse': 'Rev'
    }
    keypress = valid_actions.get(action.lower())
    if keypress:
        send_roku_command(f'keypress/{keypress}')
    else:
        print(f"Invalid playback action: {action}")


def adjust_volume(change_amount):
    """
    Adjusts the volume on the Roku TV.

    Args:
        change_amount (int): Positive to increase volume, negative to decrease volume.
    """
    if change_amount > 0:
        for _ in range(abs(change_amount)):
            send_roku_command('keypress/VolumeUp')
    elif change_amount < 0:
        for _ in range(abs(change_amount)):
            send_roku_command('keypress/VolumeDown')
    else:
        print("Volume change amount is zero; no action taken.")


def set_volume(level):
    """
    Sets the volume on the Roku TV to a specific level.

    Args:
        level (int): Desired volume level (e.g., 0 to 100).
    """
    # Roku API doesn't support setting volume directly; simulate by adjusting from current level
    print("Direct volume setting is not supported via Roku API.")


def change_channel(channel_number):
    """
    Changes the channel on the Roku TV to the specified channel number.

    Args:
        channel_number (str): The number of the channel to change to.
    """
    send_roku_command(f'keypress/Channel{channel_number}')


def select_input(input_name):
    """
    Selects a specific input on the Roku TV (e.g., HDMI1, HDMI2).

    Args:
        input_name (str): The name of the input to select (e.g., 'HDMI1', 'AV1').
    """
    send_roku_command(f'keypress/Input{input_name}')


def navigate(direction):
    """
    Navigates the Roku TV interface (up, down, left, right, select).

    Args:
        direction (str): The direction to navigate ('up', 'down', 'left', 'right', 'select').
    """
    valid_directions = ['up', 'down', 'left', 'right', 'select']
    if direction.lower() in valid_directions:
        send_roku_command(f'keypress/{direction.capitalize()}')
        print(direction)
    else:
        print(f"Invalid navigation direction: {direction}")


def back():
    """
    Sends the 'Back' command to return to the previous screen.
    """
    send_roku_command('keypress/Back')


def home():
    """
    Sends the 'Home' command to return to the Roku home screen.
    """
    send_roku_command('keypress/Home')


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
    # Roku API doesn't directly support setting a sleep timer; simulate via keypresses if possible
    print("Setting sleep timer is not supported via Roku API.")


def set_closed_captioning(state):
    """
    Sets the closed captioning state on the Roku TV.

    Args:
        state (str): The state of the closed captioning ('On', 'Off', 'OnReplay').
    """
    valid_states = ['on', 'off', 'onreplay']
    if state.lower() in valid_states:
        send_roku_command(f'keypress/CC{state.capitalize()}')
    else:
        print(f"Invalid closed captioning state: {state}")


def find_remote():
    """
    Sends a command to the Roku TV to play a sound on the remote for locating it.
    """
    send_roku_command('findremote')


def toggle_power():
    """
    Toggles the power of the Roku TV (on/off).
    """
    send_roku_command('keypress/Power')


def find_amount(user_input: str) -> int:
    """
    Determines the amount to adjust the volume based on the user's natural language input.

    Args:
        user_input (str): The user's input describing how much to adjust the volume.

    Returns:
        int: The amount to adjust the volume.
    """
    # Prompt to interpret user's input
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that helps control the volume for a Roku TV. "
                "Interpret the user's input and determine how much to increase or decrease the volume. "
                "Consider both specific numbers and qualitative terms like 'a lot', 'a bit', 'slightly', 'moderately', 'significantly', etc. "
                "For example, interpret 'turn it up a lot' as an increase by 5, 'turn it up a bit' as an increase by 2, "
                "'turn it down slightly' as a decrease by 1, etc. If the user says 'max', increase by 10, and if they say 'none', do not change the volume. "
                "Always return a single number representing the steps to adjust the volume."
            )
        },
        {"role": "user", "content": user_input}
    ]

    # Get the response from ChatGPT
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.5  # Allows for some variability in interpretation
    )

    amount_str = response.choices[0].message.content.strip()

    try:
        # Convert the response to an integer
        amount = int(amount_str)
        return amount
    except ValueError:
        # Default to 1 if unable to parse the amount
        return 1

def volume_up(input: str):
    """
    Increases the volume on the Roku TV based on user input.
    """
    # Determine the amount to increase the volume
    amount = find_amount(input)

    # Loop to send the 'VolumeUp' command the specified number of times
    for _ in range(amount):
        send_roku_command('keypress/VolumeUp')


def volume_down(input: str):
    """
    Decreases the volume on the Roku TV based on user input.
    """
    # Determine the amount to decrease the volume
    amount = abs(find_amount(input))  
    print(amount)

    # Loop to send the 'VolumeDown' command the specified number of times
    for _ in range(amount):
        send_roku_command('keypress/VolumeDown')



# Functions to extract details from user input using ChatGPT

def extract_app_name(user_input):
    """
    Extracts the app name from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The app name, or None if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts app names from user requests for a Roku TV. "
                "Extract the name of the app the user wants to open from the following input. "
                "If you cannot find an app name, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=10,
        temperature=0.0
    )

    app_name = response.choices[0].message.content.strip()
    if app_name.lower() == 'none':
        return None
    return app_name


def extract_playback_action(user_input):
    """
    Extracts the playback action from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The playback action, or None if not found.
    """
    possible_actions = ['play', 'pause', 'fast forward', 'rewind', 'stop', 'forward', 'reverse']
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts playback actions from user requests for a Roku TV. "
                "Extract the playback action (e.g., play, pause, fast forward, rewind) from the following input. "
                "Your response should be one of these actions: " + ", ".join(possible_actions) + ". "
                "If you cannot find an action, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    action = response.choices[0].message.content.strip().lower()
    if action in possible_actions:
        return action
    else:
        return None


def extract_volume_change(user_input):
    """
    Extracts the volume change amount from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        int: The volume change amount (positive for increase, negative for decrease), or 0 if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that determines how much to adjust the volume based on the user's request for a Roku TV. "
                "Extract the volume change amount from the following input. Use positive integers for increasing volume and negative integers for decreasing volume. "
                "If the user says 'increase volume by 5', respond with '5'. If they say 'turn down the volume by 3', respond with '-3'. "
                "If no specific amount is mentioned but an increase or decrease is implied, assume a default of 1 or -1. "
                "If you cannot determine a change, respond with '0'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    volume_change_str = response.choices[0].message.content.strip()
    try:
        volume_change = int(volume_change_str)
        return volume_change
    except ValueError:
        return 0


def extract_channel_number(user_input):
    """
    Extracts the channel number from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The channel number, or None if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts channel numbers from user requests for a Roku TV. "
                "Extract the channel number from the following input. "
                "If you cannot find a channel number, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    channel_number = response.choices[0].message.content.strip()
    if channel_number.lower() == 'none':
        return None
    return channel_number


def extract_input_name(user_input):
    """
    Extracts the input name from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The input name (e.g., 'HDMI1'), or None if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts input names from user requests for a Roku TV. "
                "Extract the input name (e.g., HDMI1, HDMI2, AV1) from the following input. "
                "If you cannot find an input name, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=10,
        temperature=0.0
    )

    input_name = response.choices[0].message.content.strip()
    if input_name.lower() == 'none':
        return None
    return input_name


def extract_navigation_direction(user_input):
    """
    Extracts the navigation direction from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The navigation direction ('up', 'down', 'left', 'right', 'select'), or None if not found.
    """
    valid_directions = ['up', 'down', 'left', 'right', 'select']
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts navigation directions from user requests for a Roku TV. "
                "Extract the navigation direction from the following input. "
                "Your response should be one of these directions: " + ", ".join(valid_directions) + ". "
                "If you cannot find a direction, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    direction = response.choices[0].message.content.strip().lower()
    if direction in valid_directions:
        return direction
    else:
        return None


def extract_sleep_timer_duration(user_input):
    """
    Extracts the sleep timer duration from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        int: The number of minutes, or None if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts sleep timer durations from user requests for a Roku TV. "
                "Extract the number of minutes from the following input. "
                "If you cannot find a duration, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    duration_str = response.choices[0].message.content.strip()
    if duration_str.lower() == 'none':
        return None
    try:
        duration = int(duration_str)
        return duration
    except ValueError:
        return None


def extract_captioning_state(user_input):
    """
    Extracts the closed captioning state from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        str: The captioning state ('On', 'Off', 'OnReplay'), or None if not found.
    """
    valid_states = ['on', 'off', 'onreplay']
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts closed captioning states from user requests for a Roku TV. "
                "Extract the captioning state from the following input. "
                "Your response should be one of these states: " + ", ".join(valid_states) + ". "
                "If you cannot find a state, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    state = response.choices[0].message.content.strip().lower()
    if state in valid_states:
        return state.capitalize()
    else:
        return None


def extract_volume_level(user_input):
    """
    Extracts the desired volume level from the user's input.

    Args:
        user_input (str): The user's natural language input.

    Returns:
        int: The volume level, or None if not found.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts volume levels from user requests for a Roku TV. "
                "Extract the desired volume level (e.g., 10, 50) from the following input. "
                "If you cannot find a volume level, respond with 'None'."
            )
        },
        {"role": "user", "content": user_input}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )

    volume_level_str = response.choices[0].message.content.strip()
    if volume_level_str.lower() == 'none':
        return None
    try:
        volume_level = int(volume_level_str)
        return volume_level
    except ValueError:
        return None

