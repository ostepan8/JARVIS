import asyncio
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from alarmclock import EventScheduler
# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')
api_key = os.getenv('ELEVEN_LABS_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
uri = os.getenv('MONGO_URI')

# Initialize MongoDB client, database, and other clients
mongo_client = None
db = None
openai_client = None
elevenlabs_client = None
scheduler = None

async def initialize():
    global mongo_client, db, openai_client, elevenlabs_client, scheduler

    print("Initializing system core modules...")

    # Initialize MongoDB client
    if mongo_client is None:
        try:
            print("Connecting to secure database...")
            mongo_client = MongoClient(uri, server_api=ServerApi('1'))
            mongo_client.admin.command('ping')
            print("Database connection established.")
            db = mongo_client["JARVIS"]
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e
    # Initialize OpenAI client
    if openai_client is None:
        try:
            openai_client = OpenAI(api_key=openai_api_key)  
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            raise e

    # Initialize Eleven Labs client
    if elevenlabs_client is None:
        try:
            elevenlabs_client = ElevenLabs(api_key=api_key)  
        except Exception as e:
            print(f"Error initializing Eleven Labs client: {e}")
            raise e
        # Initialize Event Scheduler
    if scheduler is None:
        try:
            time_zone = get_location_timezone()
            print(time_zone)
            scheduler = EventScheduler(time_zone = time_zone)
            print("Schedule calibrated.")
        except Exception as e:
            print(f"Error initializing event scheduler: {e}")
            raise e
    print("All systems online.")

import requests
from timezonefinder import TimezoneFinder

def get_location_timezone():
    # Step 1: Get your IP-based location using a free service
    try:
        response = requests.get('http://ip-api.com/json')
        data = response.json()
        latitude = data.get('lat')
        longitude = data.get('lon')

        if latitude is None or longitude is None:
            print("Could not determine location based on IP.")
            return None

        # Step 2: Find the time zone using latitude and longitude
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=latitude, lng=longitude)

        return timezone
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_db():
    global db
    if db is None:
        raise Exception("Database is not initialized. Please run the initialize function first.")
    return db
def get_scheduler():
    global scheduler
    if scheduler is None:
       raise Exception("Scheduler is not initialized. Please run the initialize function first.") 
    return scheduler
async def shutdown():
    global mongo_client, openai_client, elevenlabs_client

    print("Shutting down all system components...")

    # Close the MongoDB client
    if mongo_client:
        try:
            mongo_client.close()
            print("MongoDB client successfully closed.")
        except Exception as e:
            print(f"Error closing MongoDB client: {e}")

    # Clean up OpenAI client
    openai_client = None
    print("OpenAI client successfully shut down.")

    # Clean up Eleven Labs client
    elevenlabs_client = None
    print("Eleven Labs client successfully shut down.")

    print("All systems are now offline.")
