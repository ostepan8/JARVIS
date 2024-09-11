from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from pytz import utc, timezone

class EventScheduler:
    def __init__(self, time_zone='US/Central'):
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
        from pytz import utc, timezone  # Import UTC and local timezone from pytz
        from datetime import datetime

        # Define your local timezone (e.g., 'America/Chicago')
        local_tz = self.time_zone 

        # Parse the event time string to a datetime object
        event_time_local = datetime.strptime(event_time_str, '%Y-%m-%d %I:%M %p')

        # Make the datetime object timezone-aware
        event_time_local = local_tz.localize(event_time_local)

        # Convert event time to UTC
        event_time_utc = event_time_local.astimezone(utc)

        # Schedule the job with the correct function and arguments
        self.scheduler.add_job(
            callback,
            'date',
            run_date=event_time_utc,
            args=[event_name]  # Make sure the args match the function's parameters
        )
        print(f"Alarm set for: {event_time_local.strftime('%Y-%m-%d %I:%M %p')} Eastern Time - Event: {event_name}")


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
        if(self.sorted_non_recurring_events):
            earliest_non_recurring = self.sorted_non_recurring_events[0]
            non_recurring_time = earliest_non_recurring.get("event_time")
            nonrecurring_time_dt = datetime.strptime(non_recurring_time, '%Y-%m-%d %I:%M %p')

        # Find the earliest recurring event
        if self.recurring_events:
            earliest_recurring_event, day = self.find_earliest_recurring_event()
            recurring_time = self.recurring_event_into_time_string(earliest_recurring_event, day)
            recurring_time_dt = datetime.strptime(recurring_time, '%Y-%m-%d %I:%M %p')

        # Compare and return the earliest event
        if nonrecurring_time_dt and recurring_time_dt:
            if nonrecurring_time_dt <= recurring_time_dt:
                print(nonrecurring_time_dt, "RETURNING EARLIEST NON-RECURRING EVENT")
                return earliest_non_recurring, non_recurring_time
            else:
                print(recurring_time, "RETURNING EARLIEST RECURRING EVENT")
                return earliest_recurring_event,recurring_time
        elif nonrecurring_time_dt:
            print(earliest_nonrecurring, "RETURNING EARLIEST NON-RECURRING EVENT (NO RECURRING EVENTS)")
            return earliest_nonrecurring,non_recurring_time
        elif recurring_time_dt:
            print(recurring_time, "RETURNING EARLIEST RECURRING EVENT (NO NON-RECURRING EVENTS)")
            return earliest_recurring_event, recurring_time
        else:
            print("NO EVENTS FOUND")
            return None, None

    

    def find_earliest_recurring_event(self):
        """
        Find the earliest recurring event from the list of recurring events.
        """
        from datetime import datetime, timedelta
        # Get the current time
        current_time = datetime.now()
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_day_index = days_of_week.index(current_time.strftime('%A').lower())

        # Reorder days of the week so that today is at index 0
        reordered_days = days_of_week[current_day_index:] + days_of_week[:current_day_index]

        # Initialize variables to store the earliest event details
        min_time = float('inf')
        earliest_event = None
        earliest_day = None



        # Loop through the reordered days of the week
        for day in reordered_days:
            # Loop through each recurring event
            for event in self.recurring_events:
                # Get the recurrence types for this event
                recurrence_types = event.get('recurrence_type', '').lower().split('/')

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
    
    def recurring_event_into_time_string(self, event, current_day):

        from datetime import datetime, timedelta
        from bson import ObjectId

        """
        Returns the next occurrence of the event in the format "yyyy-mm-dd H:MM am/pm".
        
        Parameters:
        - event: A dictionary containing event details.
        - current_day: A lowercase string representing the current day of the week.
        """
        # Extract event details
        event_time_str = event.get('event_time', '')
        recurrence_type = event.get('recurrence_type', '').lower()
        
        # Convert event time string to a datetime object for formatting
        event_time = datetime.strptime(event_time_str, '%I:%M %p')

        # Get the current day of the week as an integer (Monday=0, ..., Sunday=6)
        current_day_index = datetime.strptime(current_day.capitalize(), '%A').weekday()

        # Parse recurrence type to get days of the week
        recurrence_days = [day.strip().split()[1].lower() for day in recurrence_type.split('/') if day.strip().startswith('weekly')]
        recurrence_days_indices = [datetime.strptime(day.capitalize(), '%A').weekday() for day in recurrence_days]

        # Check if the provided day is in the recurrence days
        if current_day.lower() not in recurrence_days:
            return "The event does not recur on the specified day."

        # Find the next occurrence day index
        today = datetime.now()
        today_index = today.weekday()

        # Calculate the number of days until the next occurrence of the specified day
        days_until_next_occurrence = (current_day_index - today_index) % 7

        # Calculate the date of the next occurrence
        next_occurrence_date = today + timedelta(days=days_until_next_occurrence)

        # Combine the next occurrence date with the event time
        next_event_time = next_occurrence_date.replace(hour=event_time.hour, minute=event_time.minute)

        # Format the output time string
        formatted_time = next_event_time.strftime('%Y-%m-%d %I:%M %p')

        return formatted_time



    def schedule_next_earliest_event(self):
        """
        Find the next earliest event and schedule an alarm for it.
        """
        # Find the next earliest event
        next_event, time_of_next_event = self.find_next_earliest_event()

        if next_event:
            self.event = next_event
            self.schedule_alarm(time_of_next_event, self.wake_up_alarm, next_event.get("description"))
        else:
            print("Nothing scheduled for today.")

    def wake_up_alarm(self, event_name):
        """
        The function that will be called when the alarm goes off.
        """
        print(f"Wake up! It's time for: {event_name}")

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
            
            # Optionally, print the result of each removal
            print(result)


