import asyncio
from system import initialize
asyncio.run(initialize())  # noqa
from interactions import analyze_and_update_profile, store_interaction
from system import initialize, elevenlabs_client, get_scheduler, swe
import re
from tv_controller import handle_tv_command
from ask_gpt import get_main_intent, ask_gpt
from scheduling import handle_add_to_schedule, handle_remove_from_schedule, summarize_events, handle_add_to_recurring_schedule
from elevenlabs import play
import simpleaudio as sa
import numpy as np
import pyaudio
import struct
import pvporcupine
import speech_recognition as sr
from dotenv import load_dotenv
import os
from file_system import handle_file_system
import threading

# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')

USER = "sir"
scheduler = get_scheduler()


def speak(text):
    audio = elevenlabs_client.generate(text=text, voice="George")
    play(audio)


def play_beep():
    frequency = 1000  # Frequency of the beep (in Hz)
    duration = 0.2  # Duration of the beep (in seconds)
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    beep = np.sin(frequency * 2 * np.pi * t)
    beep *= 32767 / np.max(np.abs(beep))
    beep = beep.astype(np.int16)
    play_obj = sa.play_buffer(beep, 1, 2, sample_rate)
    play_obj.wait_done()


def takeCommand():
    print("take command")
    r = sr.Recognizer()
    play_beep()
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


def ConversationFlow(test_mode=False, user_id="ostepan8"):
    def jarvis_input(prompt_message: str) -> str:
        return input(prompt_message+"\n") if test_mode else takeCommand()

    def jarvis_output(prompt_message: str):
        return print(prompt_message) if test_mode else takeCommand(prompt_message)

    userSaid = jarvis_input("Enter your command: ")

    if userSaid:
        # List of categories
        categories = [
            'Remove from schedule',
            'Retrieve information about schedule',
            'Add to schedule',
            'Add to recurring schedule',
            'Home Automation',
            'Security and Surveillance',
            'System Diagnostics and Reports',
            'User Information Retrieval',
            'Control Home TV',
            'Software Project Management and Help',
            'File System',
            'Other',

        ]
        intent = get_main_intent(userSaid, categories)

        # Remove any characters that aren't part of the alphabet
        intent = re.sub(r'[^a-zA-Z\s]', '', intent)
        response = ""
        if intent == "Remove from schedule":
            response = handle_remove_from_schedule(
                userSaid, take_command=input, speak=jarvis_output)
            scheduler.initialize()
        elif intent == "Retrieve information about schedule":
            response = summarize_events(userSaid, jarvis_input, jarvis_output)
        elif intent == "Add to schedule":
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
        elif intent == "Software Project Management and Help":
            swe.handle_swe_input(userSaid, jarvis_input, jarvis_output)
        elif intent == "File System":
            handle_file_system(userSaid)

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
            response = ask_gpt(userSaid, user_personalized=True,
                               previous_interactions=True, interaction_limit=10)
        jarvis_output(response)
        store_interaction(user_id, userSaid, response, intent)
        thread = threading.Thread(
            target=analyze_and_update_profile, args=(user_id, userSaid, response))
        thread.start()


def main(test=False):
    porcupine = None
    pa = None
    audio_stream = None

    print("Ready for your commands, sir.")
    if (test):
        while True:
            ConversationFlow(test)
    else:
        try:
            porcupine = pvporcupine.create(
                keywords=["jarvis"], access_key=access_key)
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            while True:
                pcm = audio_stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    ConversationFlow(test)

        finally:
            if porcupine is not None:
                porcupine.delete()
            if audio_stream is not None:
                audio_stream.close()
            if pa is not None:
                pa.terminate()


if __name__ == "__main__":
    # Now run the main function after initialize completes
    main(True)
