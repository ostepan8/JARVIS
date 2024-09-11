import re
from language_process import extract_and_parse_time, parse_event
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor
from ask_gpt import classify_intent, extract_event_and_time, schedule_retriever_interpreter
from datetime import datetime
from pytz import utc
from system import get_db
db = get_db()

events_collection = db['schedule']
recurring_events_collection =  db['recurring']

# Function to retrieve all future regular and recurring events
def get_upcoming_events(recurr = False):
    return_events = None
    if(recurr):
        return_events = list(recurring_events_collection.find())
    else:
        return_events = list(events_collection.find()) 
    return return_events


# Function to set reminders, alarms, and calendar events
def set_event(event_time, event_name, duration,is_homework):
    # Insert event into the MongoDB collection
    event = {
        "description": event_name,
        "event_time": event_time,
        "duration": duration,
        "is_homework": is_homework
    }
    events_collection.insert_one(event)
    
    return f"{event_name.capitalize()} set for {event_time}."

# Function to retrieve events based on a time query or event description
def get_events(query):
    # Try finding events by event time
    events_by_time = list(events_collection.find({"event_time": {"$regex": query, "$options": "i"}}))
    events_by_name = list(events_collection.find({"description": {"$regex": query, "$options": "i"}}))

    results = events_by_time + events_by_name

    if not results:
        return "No events found matching that query."
    
    return "\n".join([f"{event['event_type'].capitalize()}: {event['description']} at {event['event_time']}" for event in results])


def query_event(word):
    # Run the query for a single word
    return list(events_collection.find({"description": {"$regex": word, "$options": "i"}}))


def get_event(time=None, event=None):
    if not event:
        return "No event specified."

    event_words = event.lower().split()

    # Run parallel queries for each word in the event description
    with ThreadPoolExecutor() as executor:
        query_results = list(executor.map(query_event, event_words))

    # Flatten the list of results
    flattened_results = [item for sublist in query_results for item in sublist]

    if not flattened_results:
        return "No events found matching that query."

    def match_score(result):
        description = result['description'].lower()
        score = 0

        # Score based on word matches in the event description
        for word in event_words:
            if word in description:
                score += 1

        # Add weight for time match
        if time and time in result['event_time']:
            score += 2

        return score

    # Filter results to only include those that match both the event and the time
    filtered_results = [
        result for result in flattened_results
        if all(word in result['description'].lower() for word in event_words)
        and (time in result['event_time'] if time else True)
    ]

    if not filtered_results:
        return "No events found matching both the event and time."

    # Sort by match score first, and by event time second (earliest time prioritized)
    sorted_results = sorted(
        filtered_results,
        key=lambda x: (match_score(x), x['event_time']),
        reverse=True
    )

    # Return the event with the best match and the earliest time
    best_match = sorted_results[0]
    return best_match



# Function to remove events by ID, time, or description
def remove_event(query=None, event_id=None):
    if event_id:
        # Try removing by event ID
        try:
            result = events_collection.delete_one({"_id": ObjectId(event_id)})
            if result.deleted_count > 0:
                return f"Deleted event with ID '{event_id}'."
            else:
                return f"No event found with ID '{event_id}'."
        except Exception as e:
            return f"Error: {e}"

    # If no ID is provided, fallback to removing by time or description
    if query:
        result = events_collection.delete_many({
            "$or": [
                {"description": {"$regex": query, "$options": "i"}},
                {"event_time": {"$regex": query, "$options": "i"}}
            ]
        })

        if result.deleted_count > 0:
            return f"Deleted {result.deleted_count} event(s) matching '{query}'."
        else:
            return "No events found to delete."
    
    return "Please provide either an event ID or a query to delete."

# Function to set recurring reminders, alarms, and calendar events
def set_recurring_event(event_time, event_name, recurrence_type, duration, is_homework):
    # Insert recurring event into the MongoDB collection
    event = {
        "description": event_name,
        "event_time": event_time,
        "recurrence_type": recurrence_type,  # e.g., 'daily', 'weekly', 'monthly'
        "duration":duration,
        "is_homework":is_homework
    }
    recurring_events_collection.insert_one(event)
    
    return f"{event_name.capitalize()} set for {event_time} with recurrence '{recurrence_type}'."


# Function to retrieve recurring events based on a time query or event description
def get_recurring_events(query):
    # Try finding recurring events by event time or description
    events_by_time = list(recurring_events_collection.find({
        "$and": [
            {"event_time": {"$regex": query, "$options": "i"}},
            {"recurrence_type": {"$exists": True}}
        ]
    }))
    
    events_by_name = list(recurring_events_collection.find({
        "$and": [
            {"description": {"$regex": query, "$options": "i"}},
            {"recurrence_type": {"$exists": True}}
        ]
    }))

    results = events_by_time + events_by_name

    if not results:
        return "No recurring events found matching that query."
    
    return "\n".join([f"Recurring {event['recurrence_type'].capitalize()}: {event['description']} at {event['event_time']}" for event in results])

# Function to query recurring events by a single word in the event description
def query_recurring_event(word):
    return list(recurring_events_collection.find({
        "$and": [
            {"description": {"$regex": word, "$options": "i"}},
            {"recurrence_type": {"$exists": True}}
        ]
    }))

def get_recurring_event(time=None, event=None):
    if not event:
        return "No event specified."

    event_words = event.lower().split()

    # Run parallel queries for each word in the event description
    with ThreadPoolExecutor() as executor:
        query_results = list(executor.map(query_recurring_event, event_words))

    # Flatten the list of results
    flattened_results = [item for sublist in query_results for item in sublist]

    if not flattened_results:
        return "No recurring events found matching that query."

    def match_score(result):
        description = result['description'].lower()
        score = 0

        # Score based on word matches in the event description
        for word in event_words:
            if word in description:
                score += 1

        # Add weight for time match
        if time and time in result['event_time']:
            score += 2

        return score

    # Filter results to only include those that match both the event and the time
    filtered_results = [
        result for result in flattened_results
        if all(word in result['description'].lower() for word in event_words)
        and (time in result['event_time'] if time else True)
    ]

    if not filtered_results:
        return "No recurring events found matching both the event and time."

    # Sort by match score first, and by event time second (earliest time prioritized)
    sorted_results = sorted(
        filtered_results,
        key=lambda x: (match_score(x), x['event_time']),
        reverse=True
    )

    # Return the event with the best match and the earliest time
    best_match = sorted_results[0]
    return best_match

# Function to remove recurring events by ID, time, or description
def remove_recurring_event(query=None, event_id=None):
    if event_id:
        # Try removing by event ID
        try:
            result = recurring_events_collection.delete_one({"_id": ObjectId(event_id), "recurrence_type": {"$exists": True}})
            if result.deleted_count > 0:
                return f"Deleted recurring event with ID '{event_id}'."
            else:
                return f"No recurring event found with ID '{event_id}'."
        except Exception as e:
            return f"Error: {e}"

    # If no ID is provided, fallback to removing by time or description
    if query:
        result = recurring_events_collection.delete_many({
            "$and": [
                {
                    "$or": [
                        {"description": {"$regex": query, "$options": "i"}},
                        {"event_time": {"$regex": query, "$options": "i"}}
                    ]
                },
                {"recurrence_type": {"$exists": True}}
            ]
        })

        if result.deleted_count > 0:
            return f"Deleted {result.deleted_count} recurring event(s) matching '{query}'."
        else:
            return "No recurring events found to delete."
    
    return "Please provide either an event ID or a query to delete."


def event_to_string(event):
    # Format the event into a readable string
    description = event.get("description", "No description provided")
    event_time = event.get("event_time", "No time specified")

    return f"{description} at {event_time}"

def get_event_and_time(user_input, take_command=None, speak=None, recurrence = False):
    event_name, event_time, recurrence, duration, is_homework  = extract_event_and_time(user_input, recurrence = recurrence)

    # Prompt for missing details if necessary
    if not event_name:
        if speak:
            speak("Please specify the event name.")
        else:
            print("Please specify the event name.")
        event_name = take_command() if take_command else input("Enter event name: ")

    if not event_time:
        if speak:
            speak("Please specify the time for the event.")
        else:
            print("Please specify the time for the event.")
        event_time = take_command() if take_command else input("Enter event time: ")

    return event_name, event_time, recurrence, duration, is_homework

def handle_add_to_schedule(user_input, take_command=None, speak=None):
    event_name, event_time, recurrence,duration,is_homework  = get_event_and_time(user_input, take_command, speak)
    if not event_time:
        return "Sorry, I couldn’t determine the time for that event."
    if not event_name:
        return "Sorry, I couldn’t determine the event."
    
    set_event(event_time, event_name,duration,is_homework)
    response = f"'{event_name}' scheduled for {event_time}."
    return response

def handle_remove_from_schedule(user_input, take_command=None, speak=None):
    # Extract event details from user input
    event_name, event_time = schedule_retriever_interpreter(user_input, take_command, speak)

    # Initialize lists for the response
    removed_events_str_list = []
    removed_recurring_events_str_list = []

    # Initialize event query results
    events = []
    recurring_events = []

    # If a specific event name is provided, but not a specific time
    if event_name and not event_time:
        # Search by event name in both collections with substring matching
        events = list(events_collection.find({"description": {"$regex": f".*{event_name}.*", "$options": "i"}}))
        recurring_events = list(recurring_events_collection.find({"description": {"$regex": f".*{event_name}.*", "$options": "i"}}))

        # Remove matching events carefully by checking the exact description
        for event in events:
            if event_name.lower() in event.get('description', '').lower():
                events_collection.delete_one({"_id": event["_id"]})
                removed_events_str_list.append(f"Removed: {event.get('description', 'Unnamed Event')} on {event.get('event_time', 'Unknown Time')}")

        # Remove matching recurring events carefully by checking the exact description
        for recurring_event in recurring_events:
            if event_name.lower() in recurring_event.get('description', '').lower():
                recurring_events_collection.delete_one({"_id": recurring_event["_id"]})
                removed_recurring_events_str_list.append(
                    f"Removed: {recurring_event.get('description', 'Unnamed Event')} every {recurring_event.get('recurrence_type', 'Unknown Recurrence')} at {recurring_event.get('event_time', 'Unknown Time')}"
                )

    # If a specific event time is provided, but not a specific name
    elif event_time and not event_name:
        # Search by event time in regular events collection with substring matching
        events = list(events_collection.find())

        # Remove events carefully by checking the time
        for event in events:
            if event_time.lower() in event.get('event_time', '').lower():
                events_collection.delete_one({"_id": event["_id"]})
                removed_events_str_list.append(f"Removed: {event.get('description', 'Unnamed Event')} on {event.get('event_time', 'Unknown Time')}")

    # If both event name and time are provided
    elif event_name and event_time:
        # Search by both event name and time in regular events collection
        events = list(events_collection.find())

        # Remove events carefully by checking both the name and time
        for event in events:
            if event_name.lower() in event.get('description', '').lower() and event_time.lower() in event.get('event_time', '').lower():
                events_collection.delete_one({"_id": event["_id"]})
                removed_events_str_list.append(f"Removed: {event.get('description', 'Unnamed Event')} on {event.get('event_time', 'Unknown Time')}")

    # Convert removed regular events to string format
    for event in events:
        event_str = f"Removed: {event.get('description', 'Unnamed Event')} on {event.get('event_time', 'Unknown Time')}"
        removed_events_str_list.append(event_str)

    # Convert removed recurring events to string format
    for recurring_event in recurring_events:
        recurring_event_str = f"Removed: {recurring_event.get('description', 'Unnamed Event')} every {recurring_event.get('recurrence_type', 'Unknown Recurrence')} at {recurring_event.get('event_time', 'Unknown Time')}"
        removed_recurring_events_str_list.append(recurring_event_str)

    # Combine both lists into one response string
    combined_removed_events_str = "\n".join(removed_events_str_list + removed_recurring_events_str_list)

    # Return the combined response
    if combined_removed_events_str:
        return combined_removed_events_str
    else:
        return "No matching events found to remove."



    
  
    return response

def handle_retrieve_information(user_input, take_command=None, speak=None):
    # Use the new interpreter to extract event details from user input
    event_name, event_time = schedule_retriever_interpreter(user_input, take_command, speak)

    # Initialize lists for the response
    regular_events_str_list = []
    recurring_events_str_list = []

    # Initialize event query results
    events = []
    recurring_events = []

    # If no specific time is given, look up by event name in both collections
    if event_name and not event_time:
        # Search by event name in both collections
        events = events_collection.find({"description": {"$regex": event_name, "$options": "i"}})
        recurring_events = recurring_events_collection.find({"description": {"$regex": event_name, "$options": "i"}})

    # If no specific name is given, look up by event time in both collections
    elif event_time and not event_name:
        # Search by event time in both collections
        # Handle both exact and relative times; use regex to match times
        events = events_collection.find({"event_time": {"$regex": event_time, "$options": "i"}})

        # For recurring events, check for day matches or similar patterns
        day_of_week = None
        # Convert the date string to a datetime object
        date_object = datetime.strptime(event_time, '%Y-%m-%d')
    
        # Get the day of the week
        day_of_week = date_object.strftime('%A')
        recurring_events = recurring_events_collection.find({"recurrence_type": {"$regex": day_of_week, "$options": "i"}})

    # Convert regular events to string format
    for event in events:
        event_str = f"{event.get('description', 'Unnamed Event')} on {event.get('event_time', 'Unknown Time')}"
        regular_events_str_list.append(event_str)

    # Convert recurring events to string format
    for recurring_event in recurring_events:
        recurring_event_str = f"{recurring_event.get('description', 'Unnamed Event')} every {recurring_event.get('recurrence_type', 'Unknown Recurrence')} at {recurring_event.get('event_time', 'Unknown Time')}"
        recurring_events_str_list.append(recurring_event_str)

    # Combine both lists into one response string
    combined_events_str = "\n".join(regular_events_str_list + recurring_events_str_list)

    # Return the combined response
    if combined_events_str:
        return combined_events_str
    else:
        return "No matching events found."



def handle_add_to_recurring_schedule(user_input, take_command=None, speak=None):
    event_name, event_time, recurrence, duration, is_homework = get_event_and_time(user_input, take_command, speak, recurrence=True)
    if not event_time:
        return "Sorry, I couldn’t determine the time for that event."
    if not event_name:
        return "Sorry, I couldn’t determine the event."
    if not recurrence:
        return "Sorry, I couldn’t determine the recurrence pattern."

    set_recurring_event(event_time, event_name, recurrence,duration,is_homework)
    response = f"'{event_name}' scheduled for {event_time} with recurrence '{recurrence}'."
    
    return response
def handle_remove_from_recurring_schedule(user_input, take_command=None, speak=None):
    event_name, event_time, recurrence, duration, is_homework = get_event_and_time(user_input, take_command, speak, recurrence=True)
    event = get_recurring_event(event=event_name, time=event_time)
    if event:
        event_id = str(event["_id"])  # Extract the event ID
        remove_recurring_event(event_id=event_id)  # Remove the event using the ID
        response = f"Removed recurring event: {event_to_string(event)}"
    else:
        response = "I couldn't find a recurring event matching that description."

    return response
def handle_retrieve_recurring_information(user_input, take_command=None, speak=None):
    event_name, event_time, recurrence, duration, is_homework = get_event_and_time(user_input, take_command, speak, recurrence=True)
    event = get_recurring_event(event=event_name, time=event_time)
    response = event_to_string(event)
    return response



