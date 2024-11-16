import pvporcupine
import pyaudio
import struct
import numpy as np
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

def list_microphones():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"Device {i}: {device_info['name']} (Index: {i})")
    p.terminate()
list_microphones()