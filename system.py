from timezonefinder import TimezoneFinder
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import pytz
from datetime import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from alarmclock import EventScheduler
from software_engineer.swe import SoftwareEngineer
import certifi
from lights import YeelightController 
from modes.mode_handler import ModeHandler

# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
access_key = os.getenv('PORCUPINE_API_KEY')
api_key = os.getenv('ELEVEN_LABS_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
uri = os.getenv('MONGO_URI')

# Get Light Bulb Ip Addresses
BEDROOM_1_YEELIGHT_IP_ADDRESS = os.getenv('BEDROOM_1_YEELIGHT_IP_ADDRESS')
BEDROOM_2_YEELIGHT_IP_ADDRESS = os.getenv('BEDROOM_2_YEELIGHT_IP_ADDRESS')

MAIN_ROOM_1_YEELIGHT_IP_ADDRESS=os.getenv('MAIN_ROOM_1_YEELIGHT_IP_ADDRESS')
MAIN_ROOM_2_YEELIGHT_IP_ADDRESS= os.getenv('MAIN_ROOM_2_YEELIGHT_IP_ADDRESS')
MAIN_ROOM_3_YEELIGHT_IP_ADDRESS=os.getenv('MAIN_ROOM_3_YEELIGHT_IP_ADDRESS')
MAIN_ROOM_4_YEELIGHT_IP_ADDRESS=os.getenv('MAIN_ROOM_4_YEELIGHT_IP_ADDRESS')

KITCHEN_1_YEELIGHT_IP_ADDRESS=os.getenv('KITCHEN_1_YEELIGHT_IP_ADDRESS')
KITCHEN_2_YEELIGHT_IP_ADDRESS=os.getenv('KITCHEN_2_YEELIGHT_IP_ADDRESS')
KITCHEN_3_YEELIGHT_IP_ADDRESS=os.getenv('KITCHEN_3_YEELIGHT_IP_ADDRESS')

BATHROOM_1_YEELIGHT_IP_ADDRESS=os.getenv('BATHROOM_1_YEELIGHT_IP_ADDRESS')
BATHROOM_2_YEELIGHT_IP_ADDRESS=os.getenv('BATHROOM_2_YEELIGHT_IP_ADDRESS')
BATHROOM_3_YEELIGHT_IP_ADDRESS=os.getenv('BATHROOM_3_YEELIGHT_IP_ADDRESS')


bedroom_ip_addresses= [BEDROOM_1_YEELIGHT_IP_ADDRESS,BEDROOM_2_YEELIGHT_IP_ADDRESS,MAIN_ROOM_1_YEELIGHT_IP_ADDRESS,MAIN_ROOM_2_YEELIGHT_IP_ADDRESS,MAIN_ROOM_3_YEELIGHT_IP_ADDRESS,MAIN_ROOM_4_YEELIGHT_IP_ADDRESS,KITCHEN_1_YEELIGHT_IP_ADDRESS,KITCHEN_2_YEELIGHT_IP_ADDRESS,KITCHEN_3_YEELIGHT_IP_ADDRESS,BATHROOM_1_YEELIGHT_IP_ADDRESS,BATHROOM_2_YEELIGHT_IP_ADDRESS,BATHROOM_3_YEELIGHT_IP_ADDRESS]

# Initialize MongoDB client, database, and other clients
mongo_client = None
db = None
openai_client = None
elevenlabs_client = None
scheduler = None
swe = None
time_zone = None
light_controller = None
mode_controller = None
email_sender = None
lat = None
lon = None
city = None
region = None
country = None
test_mode = None


async def initialize():
    global time_zone, mongo_client, db, openai_client, elevenlabs_client, scheduler, swe,light_controller, mode_controller, email_sender
    global lat, lon, city, region, country

    print("Initializing system core modules...")

    # Initialize MongoDB client
    if mongo_client is None:
        try:
            print("Connecting to secure database...")
            mongo_client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
            mongo_client.admin.command('ping')
            print("Database connection established.")
            db = mongo_client["JARVIS"]
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e
    if swe is None:
        try:
            print("Feeding the Software Engineer coffee")
            swe = SoftwareEngineer()
        except Exception as e:
            print("Error in Software Engineering")
            raise e
    if light_controller is None:
        light_controller = YeelightController(bedroom_ip_addresses)
        print("Attained Control of the Lights")
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
            location_obj = get_location_timezone()
            lat = location_obj.get('latitude')
            lon = location_obj.get('longitude')
            city = location_obj.get('city')
            region = location_obj.get('region'),
            country = location_obj.get('country')
            time_zone = location_obj.get('timezone')
            scheduler = EventScheduler(time_zone=time_zone)
            print("Schedule calibrated.")
        except Exception as e:
            print(f"Error initializing event scheduler: {e}")
            raise e
    if mode_controller is None:
        try:
            mode_controller = ModeHandler()
        except Exception as e:
            print(f"Error initializing mode controller: {e}")
            raise e
    if email_sender is None:
        from notify import EmailSender
        try:
            email_sender = EmailSender()
        except Exception as e:
            print(f"Error initializing email sender: {e}")
            raise e
        
    print("All systems online.")


def get_location_timezone():
    try:
        # Get location data with IP-based service
        response = requests.get('http://ip-api.com/json')
        data = response.json()

        city = data.get('city')
        region = data.get('regionName')
        country = data.get('country')
        latitude = data.get('lat')
        longitude = data.get('lon')

        if not (latitude and longitude):
            print("Could not determine location based on IP.")
            return None

        # Get timezone
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=latitude, lng=longitude)

        # Return location details
        return {
            "city": city,
            "region": region,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# def get_location_timezone():
#     # Step 1: Get your IP-based location using a free service
#     try:
#         response = requests.get('http://ip-api.com/json')
#         data = response.json()
#         latitude = data.get('lat')
#         longitude = data.get('lon')

#         if latitude is None or longitude is None:
#             print("Could not determine location based on IP.")
#             return None

#         # Step 2: Find the time zone using latitude and longitude
#         tf = TimezoneFinder()
#         timezone = tf.timezone_at(lat=latitude, lng=longitude)

#         return timezone
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None

def get_local_time_string():
    # Set the timezone using the pytz library
    timezone = pytz.timezone(time_zone)
    
    # Get the current time in that timezone
    local_time = datetime.now(timezone)
    
    # Format the time into a readable string (e.g., "03:45 PM")
    local_time_str = local_time.strftime('%I:%M %p')
    
    # Combine the timezone name and time
    return f"{local_time_str} ({time_zone})"


def get_db():
    global db
    if db is None:
        raise Exception(
            "Database is not initialized. Please run the initialize function first.")
    return db


def get_scheduler():
    global scheduler
    if scheduler is None:
        raise Exception(
            "Scheduler is not initialized. Please run the initialize function first.")
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
def set_test_mode(boolean):
    global test_mode
    test_mode = boolean