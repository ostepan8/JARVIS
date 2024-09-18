from yeelight import Bulb, RGBTransition, Flow
from datetime import datetime
import time


class YeelightController:
    def __init__(self, ip_address):
        self.bulb = Bulb(ip_address)

    # Basic Actions
    def turn_on(self):
        self.bulb.turn_on()

    def turn_off(self):
        self.bulb.turn_off()

    def set_brightness(self, level):
        self.bulb.set_brightness(level)

    # Custom Moods
    def mood_good_morning(self):
        self.bulb.set_rgb(255, 223, 186)  # Light orange-white
        self.bulb.set_brightness(70)

    def mood_good_night(self):
        self.bulb.set_rgb(255, 180, 107)  # Dim warm color
        self.bulb.set_brightness(30)

    def mood_goodbye(self):
        self.bulb.set_rgb(255, 255, 255)  # White
        self.bulb.set_brightness(50)
        self.turn_off()

    def mood_party(self):
        transitions = [RGBTransition(255, 0, 0, duration=500),
                       RGBTransition(0, 255, 0, duration=500),
                       RGBTransition(0, 0, 255, duration=500)]
        flow = Flow(count=0, transitions=transitions)
        self.bulb.start_flow(flow)

    def mood_romantic(self):
        self.bulb.set_rgb(255, 0, 102)  # Pinkish-red color
        self.bulb.set_brightness(40)

    def mood_focus(self):
        self.bulb.set_rgb(255, 255, 255)  # Pure white
        self.bulb.set_brightness(100)

    def mood_relax(self):
        self.bulb.set_rgb(135, 206, 235)  # Light sky blue
        self.bulb.set_brightness(60)

    def mood_movie(self):
        self.bulb.set_rgb(255, 99, 71)  # Soft red-orange color
        self.bulb.set_brightness(20)

    def mood_disco(self):
        transitions = [RGBTransition(255, 20, 147, duration=300),
                       RGBTransition(75, 0, 130, duration=300),
                       RGBTransition(255, 69, 0, duration=300)]
        flow = Flow(count=0, transitions=transitions)
        self.bulb.start_flow(flow)

    def mood_reading(self):
        self.bulb.set_rgb(255, 239, 213)  # Warm white color
        self.bulb.set_brightness(80)

    def mood_software_engineering(self):
        transitions = [
            RGBTransition(0, 0, 255, duration=2000),     # Blue
            RGBTransition(255, 165, 0, duration=2000),   # Orange
            RGBTransition(0, 255, 0, duration=2000)      # Green
        ]
        flow = Flow(count=0, transitions=transitions)
        self.bulb.start_flow(flow)

    # New Normal Mode
    # Dynamic "Normal" Mode with Random Transitions
    def mood_normal(self):
        while True:
            current_time = datetime.now().hour

            if 6 <= current_time < 9:  # Morning: Gradually increasing brightness and warm color
                transition_options = [
                    [RGBTransition(255, 165, 0, duration=1000),   # Soft orange
                     # Light orange-white
                     RGBTransition(255, 223, 186, duration=3000),
                     RGBTransition(255, 255, 240, duration=5000)],  # Warm white

                    [RGBTransition(255, 183, 76, duration=1000),   # Goldenrod
                     RGBTransition(255, 228, 181, duration=3000),  # Moccasin
                     RGBTransition(255, 255, 210, duration=5000)],  # Light yellow

                    [RGBTransition(250, 214, 165, duration=1000),  # Apricot
                     RGBTransition(255, 239, 213, duration=3000),  # Warm peach
                     RGBTransition(255, 250, 240, duration=5000)]   # Linen
                ]
                chosen_transitions = random.choice(transition_options)
                self.bulb.start_flow(
                    Flow(count=1, transitions=chosen_transitions))
                self.set_brightness(80)

            elif 9 <= current_time < 17:  # Daytime: Bright, natural colors transitioning slowly
                transition_options = [
                    [RGBTransition(255, 255, 240, duration=5000),  # Warm white
                     # Soft yellow-white
                     RGBTransition(255, 255, 224, duration=5000),
                     RGBTransition(255, 250, 205, duration=5000)],  # Light yellow

                    [RGBTransition(255, 245, 238, duration=5000),  # Seashell
                     RGBTransition(255, 239, 213, duration=5000),  # Warm white
                     RGBTransition(255, 228, 181, duration=5000)],  # Moccasin

                    [RGBTransition(255, 240, 245, duration=5000),  # Lavender blush
                     RGBTransition(255, 250, 250, duration=5000),  # Snow white
                     RGBTransition(250, 250, 210, duration=5000)]   # Light goldenrod yellow
                ]
                chosen_transitions = random.choice(transition_options)
                self.bulb.start_flow(
                    Flow(count=1, transitions=chosen_transitions))
                self.set_brightness(100)

            elif 17 <= current_time < 20:  # Evening: Warm, calming tones transitioning smoothly
                transition_options = [
                    [RGBTransition(255, 140, 0, duration=5000),    # Darker orange
                     # Light salmon
                     RGBTransition(255, 160, 122, duration=5000),
                     RGBTransition(255, 228, 196, duration=5000)],  # Bisque

                    [RGBTransition(255, 99, 71, duration=5000),    # Tomato
                     RGBTransition(255, 127, 80, duration=5000),   # Coral
                     RGBTransition(255, 165, 79, duration=5000)],  # Sandy brown

                    [RGBTransition(255, 140, 105, duration=5000),  # Rosy brown
                     RGBTransition(244, 164, 96, duration=5000),   # Sienna
                     RGBTransition(205, 92, 92, duration=5000)]    # Indian red
                ]
                chosen_transitions = random.choice(transition_options)
                self.bulb.start_flow(
                    Flow(count=1, transitions=chosen_transitions))
                self.set_brightness(70)

            elif 20 <= current_time < 22:  # Late Evening: Cooler, relaxing tones with subtle transitions
                transition_options = [
                    [RGBTransition(173, 216, 230, duration=5000),  # Light blue
                     RGBTransition(135, 206, 250, duration=5000),  # Sky blue
                     RGBTransition(240, 248, 255, duration=5000)],  # Alice blue

                    [RGBTransition(176, 196, 222, duration=5000),  # Light steel blue
                     RGBTransition(70, 130, 180, duration=5000),   # Steel blue
                     RGBTransition(176, 224, 230, duration=5000)],  # Powder blue

                    [RGBTransition(0, 191, 255, duration=5000),    # Deep sky blue
                     RGBTransition(65, 105, 225, duration=5000),   # Royal blue
                     RGBTransition(135, 206, 235, duration=5000)]  # Light sky blue
                ]
                chosen_transitions = random.choice(transition_options)
                self.bulb.start_flow(
                    Flow(count=1, transitions=chosen_transitions))
                self.set_brightness(50)

            else:  # Night: Dimming blue light, with gradual reductions in brightness
                transition_options = [
                    [RGBTransition(25, 25, 112, duration=5000),    # Dim navy blue
                     # Medium blue
                     RGBTransition(0, 0, 128, duration=5000),
                     RGBTransition(0, 0, 139, duration=5000)],     # Dark blue

                    [RGBTransition(0, 0, 205, duration=5000),      # Medium blue
                     RGBTransition(0, 0, 255, duration=5000),      # Blue
                     RGBTransition(75, 0, 130, duration=5000)],    # Indigo

                    [RGBTransition(0, 0, 139, duration=5000),      # Dark blue
                     # Dim navy blue
                     RGBTransition(25, 25, 112, duration=5000),
                     RGBTransition(72, 61, 139, duration=5000)]    # Dark slate blue
                ]
                chosen_transitions = random.choice(transition_options)
                self.bulb.start_flow(
                    Flow(count=1, transitions=chosen_transitions))
                self.set_brightness(30)

            # Wait before the next update
            time.sleep(300)  # Update every 5 minutes for smoother transitions

    # Everyday Functionalities
    def good_morning(self):
        self.turn_on()
        self.mood_good_morning()

    def good_night(self):
        self.mood_good_night()
        self.turn_off()

    def goodbye(self):
        self.mood_goodbye()
