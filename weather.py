import pytz
from datetime import datetime, timezone
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
from system import time_zone
# Load environment variables from the .env file
load_dotenv()

# Retrieve access keys from the environment variables
api_key = os.getenv('WEATHER_API_KEY')


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
        print("Full API Response:")
        print(data)  # Print the entire JSON response
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
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    wind_deg = data['wind']['deg']
    visibility = data['visibility']
    sunrise_unix = data['sys']['sunrise']
    sunset_unix = data['sys']['sunset']

    # Convert Unix timestamps to human-readable time in UTC
    utc_time = datetime.fromtimestamp(sunrise_unix, timezone.utc)
    # Convert UTC time to Eastern Time
    eastern = time_zone
    sunrise_time = utc_time.astimezone(eastern).strftime('%-I:%M %p')
    utc_time = datetime.fromtimestamp(sunset_unix, timezone.utc)
    sunset_time = utc_time.astimezone(eastern).strftime('%-I:%M %p')

    # Formulate the response string
    response = (
        f"Greetings, Sir. Currently in {city}, {country}, there are {weather_description}. "
        f"The temperature is {temp:.1f}°F, feeling like {feels_like:.1f}°F. "
        f"The day's low is {temp_min:.1f}°F, and the high is {temp_max:.1f}°F. "
        f"Humidity stands at {humidity} percent. "
        f"Wind is blowing at {wind_speed:.1f} miles per hour from {wind_deg} degrees. "
        f"Visibility is around {visibility / 1000:.1f} kilometers. "
        f"Sunrise is at {sunrise_time} Eastern Time and sunset will be at {sunset_time} Eastern Time. "
        "Is there anything else I can assist you with?"
    )

    return response


# Example usage
weather_data = {
    'coord': {'lon': -71.0598, 'lat': 42.3584},
    'weather': [{'id': 801, 'main': 'Clouds', 'description': 'few clouds', 'icon': '02d'}],
    'base': 'stations',
    'main': {'temp': 69.57, 'feels_like': 69.57, 'temp_min': 67.95, 'temp_max': 71.38, 'pressure': 1024, 'humidity': 71, 'sea_level': 1024, 'grnd_level': 1020},
    'visibility': 10000,
    'wind': {'speed': 6.92, 'deg': 250},
    'clouds': {'all': 20},
    'dt': 1726234774,
    'sys': {'type': 1, 'id': 3486, 'country': 'US', 'sunrise': 1726222958, 'sunset': 1726268258},
    'timezone': -14400,
    'id': 4930956,
    'name': 'Boston',
    'cod': 200
}

formatted_response = format_weather_response(weather_data)
print(formatted_response)
