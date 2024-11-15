from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from pytz import utc, timezone
import json


class EventScheduler:
    email_sender = None
    reminder_collection = None
    def __init__(self, time_zone='US/Central'):
        from system import email_sender
        from system import get_db
        self.email_sender = email_sender
        db = get_db()
        self.reminder_collection = db['reminders']
        # Initialize the scheduler
        self.scheduler = BackgroundScheduler(timezone=utc)
        self.scheduler.start()

        # Store the time zone for use throughout the class
        self.time_zone = timezone(time_zone)

        # Initialize the scheduler
        self.initialize(True)

    def initialize(self, firstInitialize=False):
        if not firstInitialize:
            print("Re-Initializing Schedule")
        else:
            print("Initializing Schedule")

        from scheduling import get_upcoming_events
        events = get_upcoming_events(recurr=False)
        # Get the current time in the specified time zone
        current_time = datetime.now(self.time_zone)
        # Separate events into past and future arrays
        past_events = []
        future_events = []
        for event in events:
            # Parse the event time to a timezone-aware datetime object
            event_time = self.parse_event_time(event['event_time'])

            # Check if the event is in the past or future
            if event_time < current_time:
                past_events.append(event)
            else:
                future_events.append(event)

        self.sorted_non_recurring_events = sorted(
            future_events, key=lambda x: self.parse_event_time(x['event_time'])
        )
        self.remove_non_recurring_from_db(past_events)

        self.recurring_events = get_upcoming_events(recurr=True)
        self.schedule_next_earliest_event()

    def schedule_alarm(self, event_time_str, callback, event_name):
        """
        Schedule an alarm to trigger at the specified event time.

        Parameters:
        - event_time_str: The event time as a string in the format "yyyy-mm-dd H:MM am/pm".
        - callback: The function to call when the alarm triggers.
        - event_name: The name of the event.
        """

        # Define your local timezone (e.g., 'America/Chicago')
        local_tz = self.time_zone

        # Parse the event time string to a datetime object
        event_time_local = datetime.strptime(
            event_time_str, '%Y-%m-%d %I:%M %p')

        # Make the datetime object timezone-aware
        event_time_local = local_tz.localize(event_time_local)

        # Convert event time to UTC
        event_time_utc = event_time_local.astimezone(utc)

        # Schedule the job with the correct function and arguments
        self.scheduler.add_job(
            callback,
            'date',
            run_date=event_time_utc,
            args=[]
        )
        print(
            f"Alarm set for: {event_time_local.strftime('%Y-%m-%d %I:%M %p')} Eastern Time - Event: {event_name}")

    def parse_event_time(self, event_time_str):
        """
        Convert event time string to a timezone-aware datetime object.
        """
        # Parse the event time string to a naive datetime object
        naive_datetime = datetime.strptime(event_time_str, '%Y-%m-%d %I:%M %p')

        # Localize the naive datetime to the specified time zone
        return self.time_zone.localize(naive_datetime)

    def find_next_earliest_event(self):
        """
        Find the next earliest event from the combined list of regular and recurring events.
        """
        # Get the current time in the specified time zone and make it timezone-aware
        current_time = datetime.now(self.time_zone).replace(microsecond=0)

        # Initialize variables to store the earliest events
        earliest_non_recurring = None
        earliest_recurring = None
        non_recurring_time = None
        recurring_time = None
        nonrecurring_time_dt = None
        recurring_time_dt = None
        if (self.sorted_non_recurring_events):
            earliest_non_recurring = self.sorted_non_recurring_events[0]
            non_recurring_time = earliest_non_recurring.get("event_time")
            nonrecurring_time_dt = datetime.strptime(
                non_recurring_time, '%Y-%m-%d %I:%M %p')

        # Find the earliest recurring event
        if self.recurring_events:
            earliest_recurring_event, day = self.find_earliest_recurring_event()
            recurring_time = self.recurring_event_into_time_string(
                earliest_recurring_event, day)
            recurring_time_dt = datetime.strptime(
                recurring_time, '%Y-%m-%d %I:%M %p')

        # Compare and return the earliest event
        if nonrecurring_time_dt and recurring_time_dt:
            if nonrecurring_time_dt <= recurring_time_dt:

                return earliest_non_recurring, non_recurring_time
            else:
                return earliest_recurring_event, recurring_time
        elif nonrecurring_time_dt:
            return earliest_non_recurring, non_recurring_time
        elif recurring_time_dt:

            return earliest_recurring_event, recurring_time
        else:

            return None, None

    def find_earliest_recurring_event(self):
        """
        Find the earliest recurring event from the list of recurring events.
        """
        from datetime import datetime, timedelta
        # Get the current time
        current_time = datetime.now()
        days_of_week = ['monday', 'tuesday', 'wednesday',
                        'thursday', 'friday', 'saturday', 'sunday']
        current_day_index = days_of_week.index(
            current_time.strftime('%A').lower())

        # Reorder days of the week so that today is at index 0
        reordered_days = days_of_week[current_day_index:] + \
            days_of_week[:current_day_index]

        # Initialize variables to store the earliest event details
        min_time = float('inf')
        earliest_event = None
        earliest_day = None

        # Loop through the reordered days of the week
        for day in reordered_days:
            # Loop through each recurring event
            for event in self.recurring_events:
                # Get the recurrence types for this event
                recurrence_types = event.get(
                    'recurrence_type', '').lower().split('/')

                # Check if the event recurs on this day
                if any(recurrence_type.split(' ')[1] == day for recurrence_type in recurrence_types):
                    # Get the event time in minutes past midnight
                    event_time_str = event.get('event_time', '')
                    event_minutes = self.convert_time_to_number(event_time_str)
                    # Calculate current time in minutes past midnight
                    current_minutes = current_time.hour * 60 + current_time.minute
                    # Adjust for events occurring later today
                    if day == reordered_days[0] and event_minutes < current_minutes:
                        continue  # Skip past events on the current day
                    # Find the earliest event time for the matching day
                    if event_minutes < min_time:
                        min_time = event_minutes
                        earliest_event = event
                        earliest_day = day

            # If we found an event for today or any day after today, break the loop
            if earliest_event:
                break
        return earliest_event, earliest_day

    def convert_time_to_number(self, time_str):
        """
        Convert a time formatted as '9:45 AM' or '4:30 PM' to a number representing
        the total minutes past midnight.
        """
        # Parse the time string to a datetime object
        time_obj = datetime.strptime(time_str, '%I:%M %p')

        # Convert to minutes past midnight
        minutes = time_obj.hour * 60 + time_obj.minute
        return minutes

    def recurring_event_into_time_string(self, event, current_day, now=None):
        """
        Returns the next occurrence of the event on the specified day in the format "yyyy-mm-dd H:MM AM/PM".

        Parameters:
        - self: The instance of the class (to access self.time_zone).
        - event: A dictionary containing event details.
        - current_day: A string representing the day of interest (e.g., 'Monday', 'Tuesday', etc.)
        - now: Optional datetime object representing the current time, for testing purposes.
        """
        import pytz
        event_time_str = event.get('event_time', '')
        recurrence_type = event.get('recurrence_type', '').lower()

        try:
            event_time = datetime.strptime(event_time_str, '%I:%M %p').time()
        except ValueError:
            return "Invalid event time format."

        # Parse recurrence_type to get list of recurrence days
        recurrence_days = []
        for part in recurrence_type.split('/'):
            part = part.strip()
            if part.startswith('weekly'):
                tokens = part.split()
                if len(tokens) == 2:
                    day_name = tokens[1].capitalize()
                    recurrence_days.append(day_name)
                else:
                    return "Invalid recurrence type format."
            else:
                return "Unsupported recurrence type."

        current_day_cap = current_day.capitalize()
        if current_day_cap not in recurrence_days:
            return "The event does not recur on the specified day."

        if isinstance(self.time_zone, str):
            tz = pytz.timezone(self.time_zone)
        else:
            tz = self.time_zone
        if now is None:
            now = datetime.now(tz)
        else:
            now = tz.localize(now)
        today = now.date()

        # Build an ordered list of days starting from today
        days_of_week = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']
        today_weekday_index = today.weekday()  # Monday = 0, Sunday = 6
        ordered_days = days_of_week[today_weekday_index:] + \
            days_of_week[:today_weekday_index]

        # Find the number of days until the next occurrence of the current_day
        for index, day in enumerate(ordered_days):
            if day == current_day_cap:
                days_until_event = index
                break
        else:
            return "Error finding the day in the ordered list."

        # Calculate the date of the next occurrence
        next_occurrence_date = today + timedelta(days=days_until_event)

        # Combine the next occurrence date with the event time
        event_datetime = datetime.combine(next_occurrence_date, event_time)
        event_datetime = tz.localize(event_datetime)

        # Check if the event is scheduled for today and the time has already passed
        if days_until_event == 0 and now >= event_datetime:
            next_occurrence_date += timedelta(days=7)
            event_datetime = datetime.combine(next_occurrence_date, event_time)
            event_datetime = tz.localize(event_datetime)

        # Format the output time string
        formatted_time = event_datetime.strftime('%Y-%m-%d %I:%M %p')

        return formatted_time



    def schedule_next_earliest_event(self):
        """
        Find the next earliest event and schedule an alarm for it.
        """
        from ask_gpt import simple_ask_gpt
        # Find the next earliest event
        next_event, event_time = self.find_next_earliest_event()
        print(next_event, event_time, "FIRST EVENT")
        
        if not next_event:
            print("Nothing scheduled for today.")
            return
         # Construct the message for GPT prompt
        event_description = next_event.get('description', '')

        # Construct the message for GPT to determine alarm time
        prompt_message = (
            f"I have an event called {event_description} with at the following time:\n{event_time}\n"
            "Please provide the best alarm time for this event. The usual reminder time is 30 minutes before, "
            "but use context clues (e.g., airport trip needs more time)."
            " ONLY provide the alarm time in the exact format 'YYYY-MM-DD HH:MM AM/PM' with no additional text."
        )

        # Get alarm time from GPT
        gpt_response = simple_ask_gpt(prompt_message)

        # Parse GPT response for alarm time
        alarm_time = gpt_response.strip()  
        print(alarm_time, "ALARM_TIME")
        alarm_time = "2024-11-15 12:53 AM"

        # Define the callback function to be called when the alarm triggers
        def callback():
            self.wake_up_alarm(next_event=next_event)

        # Schedule the alarm
        self.event = next_event
        self.schedule_alarm(alarm_time, callback, next_event.get("description"))

        print(f"Alarm set for event '{next_event.get('description')}' at {alarm_time}")

    def wake_up_alarm(self, next_event):
        from system import city, region, country, get_local_time_string
        from ask_gpt import simple_ask_gpt
        from information_retrieval.weather import get_weather
        
        """
        The function that will be called when the alarm goes off.
        """
        
        # Fetch data
        event_description = next_event.get("description", "an event")
        event_time = next_event.get("event_time", "sometime")
        weather_data = get_weather()
        current_time = get_local_time_string()

        # Create the prompt using an f-string
        prompt = (
            f"You are JARVIS, the highly intelligent and sophisticated AI assistant, akin to the one from the Iron Man movies. "
            f"You are waking up Owen Stepan, your creator, in a manner befitting your character—calm, witty, and efficient. "
            f"Given an event titled '{event_description}' scheduled at '{event_time}', your task is to craft a personalized wake-up message that "
            f"gently rouses Owen, updates him on the event, and provides essential information with a touch of charm. "
            f"Be professional yet conversational, ensuring your message feels as though it’s part of a seamless morning routine. "
            f"Keep your response succinct, under 15 seconds of speaking, as clarity and brevity are key. "
            f"Here is the weather data for {city}, {region}, {country}: {weather_data}. "
            f"Here is the current time: {current_time}. "
            f"Speak as if you are directly addressing Owen in the most engaging and futuristic way possible, embodying the spirit of JARVIS. "
            f"ONLY RESPOND IN WORDS, SO NO SYMBOLS OR NUMBERS (no +, 1, 0, 100, /, \, OR ANY OTHER SYMBOL ), SINCE YOUR OUTPUT WILL BE SPOKEN ALOUD."
            f"Note: don't use celsius, use fahrenheit."
        )


        # Debug print to check the prompt
        print(prompt)

        # Send the prompt to GPT and handle the response
        response = simple_ask_gpt(prompt)
        print(response)

        # Output the response using JARVIS's output function
        from conversation_flow import jarvis_output
        jarvis_output(response)

        # Convert the event to string for context


        # event_str = json.dumps(next_event, default=str)

        # # Construct the message for GPT prompt
        # prompt_message = (
        #     f"I have an upcoming event with the following details:\n{event_str}\n"
        #     "Please generate an email reminder for this event, including the following details in JSON format:\n"
        #     "- 'subject': The subject of the email\n"
        #     "- 'address': The recipient email address (you can make it blank if not needed)\n"
        #     "- 'body': The body content of the email describing the event and the time\n"
        #     "e.g., earlier for an airport trip)"
        # )
        # print(prompt_message)

        # # Get response from GPT
        # gpt_response = simple_ask_gpt(prompt_message)
        # print(gpt_response, "gpt-res")

        # # Parse GPT response (assuming GPT returns structured JSON)
        # try:
        #     response_data = json.loads(gpt_response)
        #     subject = response_data.get("subject", "Reminder for your upcoming event")
        #     address = response_data.get("address", "")
        #     body = response_data.get("body", f"Reminder: {next_event.get('description')} at {next_event.get('event_time')}")
        # except json.JSONDecodeError:
        #     # Handle error if GPT response is not a valid JSON
        #     print("Error: Unable to parse GPT response")
        #     return


        # self.email_sender.send_email(
        #     to_address=address,
        #     subject=subject,
        #     body=body
        # )

        # After the alarm triggers, schedule the next one after some time
        self.initialize()
        # delete event

    def remove_non_recurring_from_db(self, past_events):
        from scheduling import remove_event

        for item in past_events:
            # Extract the event's ID
            event_id = str(item['_id'])

            # Remove the event from the database
            result = remove_event(event_id=event_id)
