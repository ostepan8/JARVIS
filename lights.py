from yeelight import Bulb, RGBTransition, Flow
from datetime import datetime
import time
import random
from concurrent.futures import ThreadPoolExecutor

class YeelightController:
    def __init__(self, ip_addresses):
        self.bulbs = [Bulb(ip) for ip in ip_addresses]

    def handle_input(self, userSaid):
        from ask_gpt import classify_intent
        light_intent = classify_intent(
            userSaid, ["Turn on lights", "Turn off lights", "Change color", "Good morning", "Good night", "Party mode", "Relax mode", "Focus mode", "Movie mode", "Disco mode", "Reading mode", "Romantic mode", "Normal mode","Software Engineering mode"]
        )
        print("INTENT", light_intent)

        # Dictionary to map intents to their respective functions
        intent_map = {
            "Turn on lights": self.turn_on,
            "Turn off lights": self.turn_off,
            "Good morning": self.mood_good_morning,
            "Good night": self.mood_good_night,
            "Party mode": self.mood_party,
            "Relax mode": self.mood_relax,
            "Focus mode": self.mood_focus,
            "Movie mode": self.mood_movie,
            "Disco mode": self.mood_disco,
            "Reading mode": self.mood_reading,
            "Romantic mode": self.mood_romantic,
            "Normal mode": self.mood_normal,
            "Software Engineering mode": self.mood_software_engineering
        }

        # Handle the intent
        if light_intent in intent_map:
            # Run the function asynchronously to avoid blocking
            from concurrent.futures import ThreadPoolExecutor
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
            "purple": (128, 0, 128),
            "orange": (255, 165, 0),
            "pink": (255, 192, 203),
            "white": (255, 255, 255),
            "warm white": (255, 244, 229),
            "cyan": (0, 255, 255),
        }

        # Extract color from user input
        words = userSaid.split()
        for word in words:
            if word.lower() in color_map:
                rgb_value = color_map[word.lower()]
                # Apply the color to all bulbs
                self._run_in_parallel(lambda bulb: bulb.set_rgb(*rgb_value))
                return
        print(f"Color in input '{userSaid}' not recognized.")




    def _run_in_parallel(self, func, *args, **kwargs):
        with ThreadPoolExecutor() as executor:
            executor.map(lambda bulb: func(bulb, *args, **kwargs), self.bulbs)

    def is_bulb_on(self):
        for bulb in self.bulbs:
            properties = bulb.get_properties()
            if(properties.get('power') != 'on'):
                return False
        return True
      

    # Basic Actions
    def turn_on(self):
        self._run_in_parallel(lambda bulb: bulb.turn_on())
        self.mood_normal()

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


    def mood_good_night(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 180, 107))  # Dim warm color
        self.set_brightness(30)

    def mood_goodbye(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 255, 255))  # White
        self.set_brightness(50)
        self.turn_off()

    def mood_party(self):
        transitions = [RGBTransition(255, 0, 0, duration=500),
                    RGBTransition(0, 255, 0, duration=500),
                    RGBTransition(0, 0, 255, duration=500)]
        flow = Flow(count=0, transitions=transitions)
        self._run_in_parallel(lambda bulb: bulb.start_flow(flow))

    def mood_romantic(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 0, 102))  # Pinkish-red color
        self.set_brightness(40)

    def mood_focus(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 255, 255))  # Pure white
        self.set_brightness(100)

    def mood_relax(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(135, 206, 235))  # Light sky blue
        self.set_brightness(60)

    def mood_movie(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 99, 71))  # Soft red-orange color
        self.set_brightness(20)

    def mood_disco(self):
        transitions = [RGBTransition(255, 20, 147, duration=300),
                    RGBTransition(75, 0, 130, duration=300),
                    RGBTransition(255, 69, 0, duration=300)]
        flow = Flow(count=0, transitions=transitions)
        self._run_in_parallel(lambda bulb: bulb.start_flow(flow))

    def mood_reading(self):
        self._run_in_parallel(lambda bulb: bulb.set_rgb(255, 239, 213))  # Warm white color
        self.set_brightness(80)

    def mood_software_engineering(self):
        while(True):
            transitions = [
                RGBTransition(0, 0, 255, duration=2000),     # Blue
                RGBTransition(255, 165, 0, duration=2000),   # Orange
                RGBTransition(0, 255, 0, duration=2000)      # Green
            ]
            flow = Flow(count=0, transitions=transitions)

            self._run_in_parallel(lambda bulb: bulb.start_flow(flow))
            time.sleep(2)

    # New Normal Mode
    def mood_normal(self):
        # Define three different lists of colors for different times of the day

        # Morning colors: Lightish orange, yellow, and bright colors
        morning_colors = [
            (255, 165, 0),    # Orange
            (255, 223, 186),  # Light orange-white
            (255, 255, 240),  # Warm white
            (255, 183, 76),   # Goldenrod
            (250, 214, 165),  # Apricot
            (255, 239, 213),  # Warm peach
            (255, 250, 205),  # Light yellow
            (255, 245, 238),  # Seashell
            (255, 240, 245),  # Lavender blush
        ]

        # Daytime colors: Bright, natural white and super bright colors
        daytime_colors = [
            (255, 255, 240),  # Warm white
            (255, 255, 224),  # Light yellow-white
            (255, 250, 250),  # Snow white
            (255, 255, 255),  # Pure white
            (250, 250, 240),  # Ivory
            (245, 245, 245),  # Light grayish white
            (240, 248, 255),  # Alice blue
            (255, 255, 245),  # Soft white
            (250, 240, 230),  # Linen white
        ]

        # Evening/Night colors: Blue, purple, and dark colors
        evening_colors = [
            (0, 0, 128),   # Navy blue
            (0, 0, 139),   # Dark blue
            (0, 0, 205),   # Medium dark blue
            (0, 0, 255),   # Bright blue
            (25, 25, 112), # Midnight blue
            (0, 51, 102),  # Deep sea blue
            (0, 0, 180),   # Rich dark blue
            (0, 0, 170),   # Sapphire blue
        ]


        last_color = None  # Initially, no color is set

        while True:
            current_time = datetime.now().hour

            # Randomly choose a color based on the time of day
            if 6 <= current_time < 9:  # Morning
                color_list = morning_colors
            elif 9 <= current_time < 17:  # Daytime
                color_list = daytime_colors
            else:  # Evening/Night
                color_list = evening_colors

            # Pick a random color from the chosen list
            next_color = random.choice(color_list)


            # Ensure we don't transition to the same color
            if next_color == last_color:
                next_color = random.choice([color for color in color_list if color != last_color])

            # Define the transition from the last color (if exists) to the next color
            if last_color is not None:
                transition = [RGBTransition(*last_color, duration=5000),  # Transition from last color
                            RGBTransition(*next_color, duration=5000)]  # To the next color
            else:
                transition = [RGBTransition(*next_color, duration=5000)]  # Initial transition to the next color
           
            # Run the transition in parallel for all bulbs
            flow = Flow(count=1, transitions=transition)
            self._run_in_parallel(lambda bulb: bulb.start_flow(flow))
            time.sleep(5)
            self._run_in_parallel(lambda bulb: bulb.set_rgb(*next_color))
            # time.sleep(3)



            # After the flow finishes, set the LED to the final color (next_color)
            

            # Update last color to the current one
            last_color = next_color



    # Everyday Functionalities
    def good_morning(self):
        self.turn_on()
        self.mood_good_morning()

    def good_night(self):
        self.mood_good_night()
        self.turn_off()

    def goodbye(self):
        self.mood_goodbye()
