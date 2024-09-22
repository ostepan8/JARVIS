from yeelight import *
import datetime
from concurrent.futures import ThreadPoolExecutor
import string
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

class YeelightController:
    current_intent = "None"
    current_job = None  
    
    # Static time intervals for different moods
    INTERVAL_MORNING = 6
    INTERVAL_AFTERNOON = 12
    INTERVAL_EVENING = 18

    def __init__(self, ip_addresses):
        self.bulbs = [Bulb(ip) for ip in ip_addresses]
        self.scheduler = BackgroundScheduler()  # Scheduler for mood changes

    def stop_all_threads(self):
        # Set the stop flag to indicate that all threads should stop
        self.stop_event.set()

    def handle_input(self, userSaid):
        from ask_gpt import classify_intent
        light_intent = classify_intent(
            userSaid, ["Turn on lights", "Turn off lights", "Change color", "Good morning", "Normal lights", "I don't know"]
        )
        print("LIGHTS_INTENT", light_intent)
        if light_intent == "I don't know":
            return "Sorry sir, I couldn't understand your light request."
        self.cancel_current_schedule()
        
        self.current_intent = light_intent

        # Dictionary to map intents to their respective functions
        intent_map = {
            "Turn on lights": self.turn_on,
            "Turn off lights": self.turn_off,
            "Good morning": self.mood_good_morning,
            "Normal lights": self.mood_normal,
        }

        # Handle the intent
        if light_intent in intent_map:
            # Run the function asynchronously to avoid blocking
            with ThreadPoolExecutor() as executor:
                executor.submit(intent_map[light_intent])
            return "On it, sir"
        
        elif light_intent == "Change color":
            # Handle color change in parallel
            self.change_color(userSaid)
            return "Changing the color, sir"

        else:
            print("No matching intent")
            return "Command not recognized, sir"

    def change_color(self, userSaid):
        # Define a dictionary of basic colors with their RGB values
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (144, 0, 255),
            "orange": (255, 149, 0),
            "pink": (255, 0, 242),
            "white": (255, 255, 255),
            "warm white": (255, 244, 229),
            "cyan": (0, 255, 255),
        }

        # Split the user's input into words
        words = userSaid.split()

        # Remove punctuation from words
        cleaned_words = [word.strip(string.punctuation) for word in words]

        # Loop through each cleaned word and check if it's in the color map
        for word in cleaned_words:
            lower_word = word.lower()
            if lower_word in color_map:
                rgb_value = color_map[lower_word]
                # Apply the color to all bulbs using parallel execution
                self._run_in_parallel(lambda bulb: bulb.set_rgb(*rgb_value))
                return
            
        print(f"Color in input '{userSaid}' not recognized.")

    def _run_in_parallel(self, func, *args, **kwargs):
        try:
            with ThreadPoolExecutor() as executor:
                executor.map(lambda bulb: func(bulb, *args, **kwargs), self.bulbs)
        except Exception as e:
            print(f"Error in parallel execution: {e}")

    def is_bulb_on(self):
        for bulb in self.bulbs:
            properties = bulb.get_properties()
            if properties.get('power') != 'on':
                return False
        return True
    def cancel_current_schedule(self):
        if self.current_job:
            self.scheduler.remove_job(self.current_job.id)  # Remove the job by its ID
            print('cancelled job')
            self.current_job = None


    def turn_on(self):
        try:
            self._run_in_parallel(lambda bulb: bulb.turn_on())
            self.mood_normal()  # Ensure this is called after bulbs are turned on
        except Exception as e:
            print(f"Error while turning on bulbs: {e}")

    def get_next_interval(self):
        """Get the next time interval based on the current time."""
        now = datetime.datetime.now()

        # Get the next interval based on the current time
        for hour in [self.INTERVAL_MORNING, self.INTERVAL_AFTERNOON, self.INTERVAL_EVENING]:
            next_interval = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if now < next_interval:
                return next_interval

        # If it's past the last interval, schedule for the next day's morning
        next_day = now + datetime.timedelta(days=1)
        return next_day.replace(hour=self.INTERVAL_MORNING, minute=0, second=0, microsecond=0)

    def schedule_next_update(self):
        next_interval = self.get_next_interval()
        print(f"Scheduling the next mood update for: {next_interval}")
        trigger = DateTrigger(run_date=next_interval)

        # Cancel the previous job before scheduling a new one
        self.cancel_current_schedule()

        # Schedule the next job and store its reference
        self.current_job = self.scheduler.add_job(self.mood_normal, trigger)


    def mood_normal(self):
        try:

            current_time = datetime.datetime.now().time()

            # Define moods based on time ranges
            if current_time >= datetime.time(self.INTERVAL_MORNING, 0) and current_time < datetime.time(self.INTERVAL_AFTERNOON, 0):
                rgb_value = (255, 223, 186)  # Warm light
            elif current_time >= datetime.time(self.INTERVAL_AFTERNOON, 0) and current_time < datetime.time(self.INTERVAL_EVENING, 0):
                rgb_value = (255, 255, 255)  # Bright light
            elif current_time >= datetime.time(self.INTERVAL_EVENING, 0) and current_time < datetime.time(22, 0):
                rgb_value = (173, 216, 230)  # Cool blue
            else:
                rgb_value = (255, 192, 203)  # Dimmed warm light
            

            # Apply the mood to all bulbs using parallel execution asynchronously
            self._run_in_parallel(lambda bulb: bulb.set_rgb(*rgb_value))
            
            # Schedule the next mood update
            self.schedule_next_update()

        except Exception as e:
            print(f"Error in mood_normal: {e}")

    def turn_off(self):
        self._run_in_parallel(lambda bulb: bulb.turn_off())

    def set_brightness(self, level):
        self._run_in_parallel(lambda bulb: bulb.set_brightness(level))

    # Custom Moods
    def mood_good_morning(self):
        def gradual_brightness_increase(bulb):
            # Start with a soft warm light
            bulb.set_rgb(255, 223, 186)  # Light orange-white
            bulb.set_brightness(10)  # Start with low brightness
            
            # Gradually increase brightness and change to white light
            for brightness in range(10, 101, 10):  # Increase brightness from 10 to 100 in steps of 10
                time.sleep(0.5)  # Adjust the time delay to control the speed of transition
                bulb.set_brightness(brightness)
            
            # Once brightness is full, transition to a super bright white light
            bulb.set_rgb(255, 255, 255)  # Bright white

        self._run_in_parallel(gradual_brightness_increase)

    def good_morning(self):
        self.turn_on()
        self.mood_good_morning()

    def start_scheduler(self):
        """Start the background scheduler."""
        self.scheduler.start()

    def stop_scheduler(self):
        """Stop the background scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            print("Scheduler stopped.")
