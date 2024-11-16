
import asyncio
from system import initialize
asyncio.run(initialize())  # noqa
from interactions import analyze_and_update_profile, store_interaction
from system import initialize, elevenlabs_client, get_scheduler, swe
import re
from tv_controller import handle_tv_command
from ask_gpt import get_main_intent, ask_gpt
from system import light_controller
from scheduling import handle_add_to_schedule, handle_remove_from_schedule, summarize_events, handle_add_to_recurring_schedule
from elevenlabs import stream
import speech_recognition as sr
from dotenv import load_dotenv
import os
import threading
from computer_control import handle_computer_control_input
from information_retrieval.info_retrieval import handle_information_finding
from system import mode_controller
from modes.modes import Mode
from elevenlabs import VoiceSettings
import os

import re
# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')

scheduler = get_scheduler()

def jarvis_input(prompt_message: str) -> str:
    from system import test_mode
    return input(prompt_message+"\n") if test_mode else takeCommand()

def jarvis_output(prompt_message: str):
    from system import test_mode
    print(prompt_message, "message", test_mode)
    return print(prompt_message) if test_mode else speak(prompt_message, "Arabella")

def ConversationFlow(command,authenticated,test_mode=False, user_id="ostepan8"):
    if(not authenticated):
        print("not authenticated, turned on glossaryck mode")
        mode_controller.current_mode = Mode.GLOSSARYCK
    else:
        if(mode_controller.current_mode == Mode.GLOSSARYCK):
            mode_controller.current_mode = Mode.JARVIS
    if(mode_controller.current_mode == Mode.JARVIS):
        jarvis_conversation_flow(command,jarvis_input, jarvis_output, user_id)
    elif(mode_controller.current_mode == Mode.TV):
        tv_conversation_flow(command=command)
    elif(mode_controller.current_mode ==  Mode.GLOSSARYCK):
        glossaryck_conversation_flow(command )

def checkModeChange(userInput: str):
    # Define a dictionary mapping keywords to modes
    mode_keywords = {
        "tv mode": Mode.TV,
        "jarvis mode": Mode.JARVIS,
        "gloss mode": Mode.GLOSSARYCK
    }

    # Normalize input
    lowerCaseInput = userInput.lower()
    
    # Check if any keyword exists in the input and set the mode accordingly
    for keyword, mode in mode_keywords.items():
        if any(phrase in lowerCaseInput for phrase in [f"turn on {keyword}", f"jarvis turn on {keyword}", f"hey jarvis turn on {keyword}"]):
            mode_controller.current_mode = mode
            return True

    # Print current mode if no changes were made
    print(mode_controller.current_mode)
    return False


def speak(text: str, voice):
    voice_id_map = {'arabella': "aEO01A4wXwd1O8GPgGlF"}

    # Stream audio response from Eleven Labs
    response_stream = elevenlabs_client.text_to_speech.convert_as_stream(
        # Sounds like jarvis
        voice_id=voice_id_map.get("arabella"), 
        optimize_streaming_latency="0",
        output_format="mp3_44100_192",
        model_id ="eleven_multilingual_v2",
        text=text,
        voice_settings=VoiceSettings(stability=.45, similarity_boost=.8, style=.05, use_speaker_boost=True)
    )
    stream(response_stream)



def takeCommand():
    print("take command")

    r = sr.Recognizer()
    # play_beep()
    with sr.Microphone() as source:
        print("Listening... ", end="")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        query = ''
        try:
            print("Recognizing... ", end="")
            query = r.recognize_google(audio, language='en-US')
            print(f"User said: {query}\n")
        except Exception as e:
            print("Exception: " + str(e))
            print("Could not understand your audio. Please try again.")
            return ""
    return query.lower()


    
def jarvis_conversation_flow(command,jarvis_input, jarvis_output, user_id):
    if(checkModeChange(command)):
        return
    userSaid = command

    if userSaid:
        # List of categories
        categories = [
            'Remove from schedule',
            'Retrieve information about schedule',
            'Add to schedule, alarm, or timer',
            'Add to recurring schedule',
            'Home Automation',
            'Security and Surveillance',
            'System Diagnostics and Reports',
            'User Information Retrieval',
            'Control Home TV',
            'Control Home Lights',
            'Software Development and File System Manager',
            'Computer Application and Website Control',
            'Other',
            'Audio Transcription Fail'
            'Weather Information'
        ]
        intent = get_main_intent(userSaid, categories)
        if(intent == 'Audio Transcription Fail'):
            from ask_gpt import simple_ask_gpt
            response = simple_ask_gpt(
            f"As JARVIS would say to Tony Stark, inform the user that their command, '{userSaid}' wasn't understood due to possible audio issues. Keep the response friendly, professional, and under 10 words. The user prefers being called sir."
            )
            jarvis_output(response)
            return

        print(intent,"INTENT")

        # Remove any characters that aren't part of the alphabet
        intent = re.sub(r'[^a-zA-Z\s]', '', intent)
        response = ""
        should_store= False
        if intent == "Remove from schedule":
            response = handle_remove_from_schedule(
                userSaid, take_command=input, speak=jarvis_output)
            scheduler.initialize()
        elif intent == "Retrieve information about schedule":
            response = summarize_events(userSaid, jarvis_input, jarvis_output)
        elif intent == 'Add to schedule alarm or timer':
            response = handle_add_to_schedule(
                userSaid, take_command=jarvis_input, speak=jarvis_output)
            scheduler.initialize()
        elif intent == "Add to recurring schedule":
            
            response = handle_add_to_recurring_schedule(
                userSaid, take_command=jarvis_input, speak=jarvis_output)
            scheduler.initialize()
        elif intent == "Control Home TV":
            handle_tv_command(userSaid)
            response = "On it, sir"
        elif intent == 'Software Development and File System Manager':
            
            response, should_store_swe_output = swe.handle_input(userSaid, jarvis_input, jarvis_output)
            should_store = should_store_swe_output
        # elif intent == "File System":
            # handle_file_system(userSaid)
        elif intent == 'Control Home Lights':
            light_controller.handle_input(userSaid)
            response = "On it, sir"
        elif intent == 'Computer Application and Website Control':
            print("handling computer")
            handle_computer_control_input(userSaid)
            response= "On it, sir"
        elif intent == 'Computer Application and Website Control':
            print("Weather Information")
            from information_retrieval.weather import get_weather
            prompt = (
                f"You are JARVIS, the highly intelligent and sophisticated AI assistant, akin to the one from the Iron Man movies. "
                f"Your task is to respond to the command: '{userSaid}' in a manner befitting your character—calm, witty, and efficient. "
                f"To assist you, here is the current weather data: {get_weather()}. "
                f"Ensure your response is conversational, clear, and suitable for being spoken aloud. "
                f"ONLY RESPOND IN WORDS, SO NO SYMBOLS OR NUMBERS (no +, one, zero, one hundred, slash, or any other symbols), SINCE YOUR OUTPUT WILL BE SPOKEN ALOUD. "
                f"Note: don't use celsius, use fahrenheit. "
                f"Respond as though you are directly addressing Owen Stepan in the most engaging and futuristic way possible, embodying the spirit of JARVIS."
            )
            response = simple_ask_gpt(prompt)


            # response = handle_home_automation(userSaid)
            # if test_mode:
            # print(f"Home Automation Response: {home_automation_response}")
            # else:
            # speak(home_automation_response)

        # elif intent == "Security and Surveillance":
            # response = handle_security(userSaid)
            # if test_mode:
            # print(f"Security Response: {security_response}")
            # else:
            # speak(security_response)

        # elif intent == "System Diagnostics and Reports":
            # response = handle_system_diagnostics(userSaid)
            # if test_mode:
            # print(f"Diagnostics Response: {diagnostics_response}")
            # else:
            # speak(diagnostics_response)

        else:
            extra_info=handle_information_finding(user_input=userSaid)
            print(extra_info, "EXTRA")
            extra_data = ""
            if(extra_info is not None):
                extra_data = extra_data +f"{extra_info}"

            response = ask_gpt(userSaid, user_personalized=True,similar_interactions=True,
                               previous_interactions=True, prev_interaction_limit=10,extra_data=extra_data)
            should_store= True
        jarvis_output(response)
        if(should_store):
            thread_store_interaction = threading.Thread(
                target=store_interaction, args=(user_id, userSaid, response, intent)
            )
            thread_store_interaction.start()

        # Analyze and update profile on a separate thread
        thread_analyze_profile = threading.Thread(
            target=analyze_and_update_profile, args=(user_id, userSaid, response)
        )
        thread_analyze_profile.start()


def tv_conversation_flow(command: str):
    if(checkModeChange(command)):
        return
    from tv_controller import home, back, instant_replay, volume_down, volume_up, toggle_power, navigate

    # Define helper functions that wrap the navigate function
    def left():
        navigate('left')

    def select():
        navigate('select')

    def right():
        navigate('right')

    def up():
        navigate('up')

    def down():
        navigate('down')
    

    # Create a mapping of functions to lists of phrases
    action_phrases = {
        left: ['left', 'l', 'L', 'go left', 'move left'],
        right: ['right', 'r', 'R', 'go right', 'move right'],
        up: ['up', 'u', 'U', 'go up', 'move up'],
        down: ['down', 'd', 'D', 'go down', 'move down'],
        select: ['select', 's', 'S', 'ok', 'enter'],
        instant_replay: ['replay', 'instant replay', 'repeat', 'again'],
        back: ['back', 'b', 'B', 'previous', 'go back'],
        home: ['home', 'h', 'H', 'main menu', 'start'],
        volume_down: ['volume down', 'vd', 'VD', 'lower volume', 'decrease volume'],
        volume_up: ['volume up', 'vu', 'VU', 'raise volume', 'increase volume'],
        toggle_power: ['turn tv on', 'turn tv off', 'power', 'p', 'P', 'toggle power']

        # Add more mappings as needed
    }

    # Normalize the command input
    normalized_command = command.strip().lower()

    # Flag to check if the command was recognized
    command_found = False

    # Iterate over the action_phrases dictionary
    for action, phrases in action_phrases.items():
        if normalized_command in phrases:
            action()  # Call the associated function
            command_found = True
            break  # Exit the loop once a match is found

    if not command_found:
        # Handle unrecognized commands
        print(f"Command '{command}' not recognized.")

def glossaryck_conversation_flow(command: str):
    from ask_gpt import simple_ask_gpt
    # Define Glossaryck's persona in the system prompt
    glossaryck_prompt = (
        "You are Glossaryck from 'Star vs. the Forces of Evil'. "
        "Your job is to annoy the user who is not authorized. Mention their lack of authorization in cryptic, unhelpful ways. "
        "Keep responses under 8 seconds of speaking time, under 15 words, and mildly connected to security. "
        "Be fast, sarcastic, and tangential, but ensure you always mock their unauthorized status. "
        f"Respond to this: {command} "
        "Maximum brevity, mention they're not authorized, but don’t provide useful info."
    )
    
    # Get the response from GPT
    response = simple_ask_gpt(glossaryck_prompt)
    speak(response, "glossy")
