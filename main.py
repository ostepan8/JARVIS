import asyncio
from system import initialize, shutdown, get_scheduler
asyncio.run(initialize())
import speech_recognition as sr
import time
import pvporcupine
import struct
import pyaudio
import pyttsx3
import numpy as np
import simpleaudio as sa
from elevenlabs import play
from interactions import analyze_and_update_profile, store_interaction
from scheduling import handle_add_to_schedule, handle_remove_from_schedule, handle_retrieve_information, handle_add_to_recurring_schedule, handle_remove_from_recurring_schedule, handle_retrieve_recurring_information
from ask_gpt import get_main_intent, ask_gpt
from tv_controller import handle_tv_command
import re
USER = "sir"
scheduler = get_scheduler()
def speak(text):
    audio = client.generate(text=text, voice="George")
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
    # If in test mode, use input() to get the user's text input from the terminal
    userSaid = input("Enter your command: ") if test_mode else takeCommand()

    if userSaid:
        # Assume this is where you're getting the intent
        intent = get_main_intent(userSaid)

        # Remove any characters that aren't part of the alphabet
        intent = re.sub(r'[^a-zA-Z\s]', '', intent)

        print(intent)
        response=""
        if intent == "Remove from schedule":
            if test_mode:
                response = handle_remove_from_schedule(userSaid, take_command=input, speak=print)
            else:
                response = handle_remove_from_schedule(userSaid, take_command, speak)
            scheduler.initialize()
        elif intent == "Retrieve information about schedule":
            # Retrieve the schedule information
            if test_mode:
                # In test mode, call the function with input/output handlers
                events_summary = handle_retrieve_information(userSaid, take_command=input, speak=print)
            else:
                # In regular mode, call the function without input/output handlers
                events_summary = handle_retrieve_information(userSaid)

            # Prepare the question for GPT to JARVIS-ify the response
            question = f"J.A.R.V.I.S., respond to the following request from Tony Stark with a brief, natural, and conversational tone. Follow these rules: sort events by time of day, only mention events relevant to today, and avoid using any lists, bullet points, or formatting. Keep it concise and focused on the essentials. The original question is: '{userSaid}'. The schedule details are: '{events_summary}'."

            # Call ask_gpt to generate a JARVIS-like response
            response = ask_gpt(question, user_personalized=True)

        elif intent == "Add to schedule":
            if test_mode:
                response = handle_add_to_schedule(userSaid, take_command=input, speak=print)
            else:
                response = handle_add_to_schedule(userSaid, take_command, speak)
            scheduler.initialize()
        elif intent == "Add to recurring schedule":
            if test_mode:
                response = handle_add_to_recurring_schedule(userSaid, take_command=input, speak=print)
            else:
                response = handle_add_to_recurring_schedule(userSaid, take_command, speak)
            scheduler.initialize()
        elif intent == "Control Home TV":
            handle_tv_command(userSaid)
            
            
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
            response = ask_gpt(userSaid, user_personalized= True, previous_interactions=True, interaction_limit=10)
        if test_mode:
            print(f"{response}")
        else:
            speak(response)
        store_interaction(user_id, userSaid, response, intent)
        analyze_and_update_profile(user_id, userSaid, response)
        



def main(test = False):
    porcupine = None
    pa = None
    audio_stream = None

    print("Ready for your commands, sir.")
    if(test):
        while True:
            ConversationFlow(test)
    else:
        try:
            porcupine = pvporcupine.create(keywords=["jarvis"], access_key=access_key)
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