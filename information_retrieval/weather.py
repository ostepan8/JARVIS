import pytz
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
import os
from system import time_zone
# Load environment variables from the .env file
load_dotenv()



# Retrieve access keys from the environment variables
api_key = os.getenv('WEATHER_API_KEY')

def get_weather():
    return format_weather_response(get_free_weather(api_key=api_key))

def get_current_location():
    """
    Fetches the current location using the ipinfo.io API.
    Returns the city, latitude, and longitude of the user.
    """
    try:
        response = requests.get("https://ipinfo.io")
        if response.status_code == 200:
            data = response.json()
            city = data['city']
            lat, lon = data['loc'].split(',')
            return city, float(lat), float(lon)
        else:
            return None, None, None
    except Exception as e:
        return None, None, None


def get_free_weather(api_key):
    """
    Fetches the weather data from OpenWeatherMap using the 2.5 weather API.
    Prints the entire JSON response.
    """
    city, lat, lon = get_current_location()
    if not city or not lat or not lon:
        return "Unable to determine location."

    # API call to the OpenWeatherMap 2.5 Weather API
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,  # You can also use 'lat' and 'lon' if you prefer location-based querying
        'appid': api_key,
        'units': 'metric'  # Use 'imperial' for Fahrenheit
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        # Print the entire JSON response
        data = response.json()

        return data  # Return the full response for further use
    else:
        try:
            error_data = response.json()
            if error_data.get('cod') == 401:
                return "Invalid API key. Please check your OpenWeatherMap API key."
            elif error_data.get('cod') == '404':
                return f"Location not found. Please provide a valid location."
            else:
                return f"Error: {error_data.get('message')}"
        except ValueError:
            return "Sorry, I couldn't fetch the weather data right now."

def format_weather_response(data):
    """
    Formats the weather data into a string that mimics a JARVIS-style response.
    """
    # Extract relevant data
    city = data['name']
    country = data['sys']['country']
    weather_description = data['weather'][0]['description']
    temp_celsius = data['main']['temp']
    feels_like_celsius = data['main']['feels_like']
    temp_min_celsius = data['main']['temp_min']
    temp_max_celsius = data['main']['temp_max']
    humidity = data['main']['humidity']
    wind_speed_mps = data['wind']['speed']
    wind_deg = data['wind']['deg']
    visibility = data['visibility']
    sunrise_unix = data['sys']['sunrise']
    sunset_unix = data['sys']['sunset']

    # Convert temperatures from Celsius to Fahrenheit
    temp = (temp_celsius * 9/5) + 32
    feels_like = (feels_like_celsius * 9/5) + 32
    temp_min = (temp_min_celsius * 9/5) + 32
    temp_max = (temp_max_celsius * 9/5) + 32

    # Convert wind speed from m/s to mph
    wind_speed = wind_speed_mps * 2.237

    # Ensure time_zone is set correctly to the 'America/New_York' timezone
    eastern = pytz.timezone(time_zone)

    # Convert Unix timestamps to human-readable time in UTC, then to Eastern Time
    utc_time = datetime.fromtimestamp(sunrise_unix, timezone.utc)
    sunrise_time = utc_time.astimezone(eastern).strftime('%-I:%M %p')

    utc_time = datetime.fromtimestamp(sunset_unix, timezone.utc)
    sunset_time = utc_time.astimezone(eastern).strftime('%-I:%M %p')

    response = (
        f"In the user's location, {city}, {country}, it's: {weather_description}. "
        f"Temperature: {temp:.1f}°F, feels like {feels_like:.1f}°F. "
        f"Low: {temp_min:.1f}°F, High: {temp_max:.1f}°F. "
        f"Humidity: {humidity}%, Wind: {wind_speed:.1f} mph from {wind_deg}°. "
        f"Visibility: {visibility / 1000:.1f} km. "
        f"Sunrise: {sunrise_time} ET, Sunset: {sunset_time} ET. "
    )

    return response







