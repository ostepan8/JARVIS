from datetime import datetime
from system import openai_client, get_db, get_local_time_string,get_location_timezone
from pytz import timezone
import re
import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")
# Initialize database connection
db = get_db()

# Define collections
interactions_collection = db['interactions']
user_collection = db['users']


def simple_ask_gpt(message):

    messages = [{"role": "user", "content": message}]

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # Return the content of the assistant's response
    return completion.choices[0].message.content


# Function to get the user's profile from the database
def get_user_profile(user_id):
    return user_collection.find_one({"user_id": user_id})

# Function to get recent interactions from the database
def get_recent_interactions(interaction_limit):
    recent_interactions = list(interactions_collection.find().sort("_id", -1).limit(interaction_limit))
    if recent_interactions:
        return "Recent Interactions: " + "; ".join(
            [
                f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]: User said: '{interaction['user_input']}', Assistant responded: '{interaction['response']}'"
                for interaction in recent_interactions
            ]
        )
    return "No recent interactions found."


# Function to extract keywords using spaCy
def extract_keywords(text):
    # Process the text using spaCy
    doc = nlp(text)
    
    # Extract keywords: Nouns, Proper Nouns, Verbs, Named Entities
    keywords = set()
    
    # Named entities
    for ent in doc.ents:
        keywords.add(ent.text)
    
    # Nouns and Verbs
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN", "VERB"):
            keywords.add(token.lemma_)  # Use lemma to get base form (e.g., "knew" -> "know")
    
    return list(keywords)

# Function to get similar interactions based on the user's question
def get_similar_interactions(question, interaction_limit=None):
    # Extract keywords from the question
    key_phrases = extract_keywords(question)
    
    # Build a regex pattern to match any of the extracted keywords
    if key_phrases:
        regex_pattern = ".*" + ".*|.*".join(re.escape(phrase) for phrase in key_phrases) + ".*"
    else:
        # If no key phrases are found, use a broad query
        regex_pattern = ".*" + re.escape(question) + ".*"
    
    # Query the collection for interactions containing the key phrases
    query = {
        "user_input": {"$regex": regex_pattern, "$options": "i"}
    }
    similar_interactions = None
    if(interaction_limit != None):
        similar_interactions = list(interactions_collection.find(query).sort("_id", -1).limit(interaction_limit))
    else:
        similar_interactions = list(interactions_collection.find(query).sort("_id", -1))
    
    # Format the results
    if similar_interactions:
        return "Similar Interactions: " + "; ".join(
            [
                f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]: User said: '{interaction['user_input']}', Assistant responded: '{interaction['response']}'"
                for interaction in similar_interactions
            ]
        )
    return "No similar interactions found."


# Main function that calls GPT and structures the conversation
def ask_gpt(question, user_personalized=False, previous_interactions=False, similar_interactions=False, user_id="ostepan8", prev_interaction_limit=0, extra_data=""):
    time_string = get_local_time_string()

    if user_personalized:
        user_profile = get_user_profile(user_id)
    else:
        user_profile = None

    creator_string = user_profile.get("name", "Owen Stepan") if user_profile else "Owen Stepan"
    preferred_name = user_profile.get("preferred_title", "sir") if user_profile else "sir"
    extra_prompt = f"An oracle provided you with this relevant data: '{extra_data}'." if extra_data else ""


    # Initialize the base messages
    base_message = (
        "You are J.A.R.V.I.S., an intelligent assistant modeled after the AI from the Iron Man movies. "
        f"Your job is to provide quick, concise, and accurate responses in a friendly and conversational tone, focusing on clarity and relevance to your creator, {creator_string}. "
        f"Your creator is named {creator_string}, not Tony Stark, however you MUST address him as his {preferred_name} in all communications. "
        f"{creator_string} is highly capable, so engage in natural, friendly dialogue, avoiding overly formal language or unnecessary details. "
        "Speak as if you’re having a casual conversation between two highly intelligent individuals. "
        "Use natural language, contractions, and expressions that make your responses feel relaxed and approachable. "
        "Avoid code snippets, diagrams, graphs, lists, bullet points, or any form of structured formatting. "
        "Please spell out any symbols that you use, as they will be spoken not seen (degrees, math operators, etc)"
        "Keep it concise, engaging, and actionable, guiding rather than instructing, and always maintain a calm, confident demeanor. "
        f"The current local time is {time_string}, which should be one of the most relevant pieces of context. "
    )


    if user_profile:
        base_message += f"User Profile: {user_profile}. "

    if previous_interactions:
        interactions_str = f"Past {prev_interaction_limit} interactions: "+ get_recent_interactions(prev_interaction_limit)
        base_message += interactions_str +" "

    if similar_interactions:
        similar_interactions_str = "Similar previous interactions found: " + get_similar_interactions(question) +" "
        base_message += similar_interactions_str
    base_message += extra_prompt

    base_message += f" Use all of this information to craft a response that answers this main question: {question}"


    messages = [{"role": "system", "content": base_message}]


    # Call GPT model to generate response
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return completion.choices[0].message.content

def ask_json(question, user_personalized=False, previous_interactions=False, user_id="ostepan8", interaction_limit=0):
    local_time = datetime.now(timezone('US/Central')
                              ).strftime('%Y-%m-%d %H:%M %p')

    # Initialize the base messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are J.A.R.V.I.S., an intelligent assistant modeled after the AI from the Iron Man movies. "
            )
        },
        {
            "role": "system",
            "content": f"The current local time is {local_time}."
        }
    ]

    # Fetch user data if user_personalized is True
    if user_personalized:
        user_profile = user_collection.find_one({"user_id": user_id})
        if user_profile:
            # Convert user profile to a JSON-like dictionary
            user_data_str = {"User Profile": user_profile}
            messages.append({"role": "system", "content": str(user_data_str)})

    # Fetch the last 10 interactions if previous_interactions is True
    if previous_interactions:
        recent_interactions = list(interactions_collection.find().sort(
            "_id", -1).limit(interaction_limit))
        if recent_interactions:
            # Format the recent interactions into a JSON-like string
            interactions_data = [
                {
                    "timestamp": interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    "user_input": interaction['user_input'],
                    "assistant_response": interaction['response']
                }
                for interaction in recent_interactions
            ]
            messages.append({"role": "system", "content": str(
                {"Recent Interactions": interactions_data})})

    # Add the user's question, asking for a JSON-formatted response
    messages.append(
        {"role": "user", "content": f"Respond to the following in JSON format: {question}"})

    # Call GPT model to generate response
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # Return the JSON response from GPT
    return completion.choices[0].message.content


def get_main_intent(text, categories, previous_interactions=True):
    # Create a system message to classify the intent
    messages = [
        {
            "role": "system",
            "content": (
                "You are an intelligent assistant. Your task is to classify the following sentence into exactly one of the following categories: "
                + ", ".join(f"'{category}'" for category in categories) + ". "
                "Return only the name of the category that best fits the given sentence, and nothing else. "
                "When making your decision, consider the context provided by recent interactions to infer the user's current preferences and priorities. "
                "For example, if a recent interaction involved scheduling a recurring event, give higher weight to the 'recurring schedule' category. "
                "Similarly, if a recent interaction involved controlling a TV, give higher weight to categories like 'Control Home TV'. "
                "Remember that 'recurring schedule' refers to events that happen regularly (such as daily, weekly, or monthly), and that 'Finding a remote' counts as 'Control Home TV'. "
                "Under no circumstances should you provide explanations, multiple categories, or any text other than the name of the category. Your response must be a single string containing only one of the categories."
                "If the prompt seems as though the microphone caught audio that does not make sense or is clearly background audio, return the 'Audio Transcription Fail' intent."
                "NOTE: Any mention of a working directory/project directory or talk of a working environment has to do with the Software intent."

            )
        },
        {"role": "user", "content": text}
    ]

    # Fetch the last 3 interactions if previous_interactions is True
    if previous_interactions:
        recent_interactions = list(
            interactions_collection.find().sort("_id", -1).limit(3))
        if recent_interactions:
            # Format the recent interactions into a readable string
            interactions_str = "Recent Interactions: " + "; ".join(
                [
                    f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]: User said: '{interaction['user_input']}', Assistant responded: '{interaction['response']}'"
                    for interaction in recent_interactions
                ]
            )
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"Use the recent interactions to understand the user's current needs and preferences, especially if the new input is unclear: {interactions_str}"
                    ),
                }
            )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=50,
        temperature=0
    )

    # Correctly access the content of the response
    intent = response.choices[0].message.content.strip()
    return intent


def classify_intent(text, categories, context_message=None, model="gpt-4o-mini"):
    """
    Classify the intent of a given text based on provided categories and context.

    Parameters:
    - text (str): The user input text to classify.
    - categories (list): A list of categories to classify the text into.
    - context_message (str): An optional context message to guide the classification.
    - model (str): The OpenAI model to use for classification.

    Returns:
    - intent (str): The classified intent.
    """
    # Build the system message
    system_message = context_message if context_message else (
        "Classify the following sentence into one of these categories: "
        f"{', '.join(categories)}."
        "ONLY RETURN THE STRING OF THE INTENT AND NOTHING ELSE."
    )

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": text}
    ]

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=50,
        temperature=0
    )

    # Extract the classified intent
    intent = response.choices[0].message.content.strip()
    return intent


def parse_event_string(event_string):
    # Initialize an empty dictionary to store the parsed data
    event_data = {}

    # Split the string into key-value pairs using the ', ' separator
    pairs = event_string.split(', ')

    # Iterate over the key-value pairs
    for pair in pairs:
        # Split each pair into key and value using the ': ' separator
        key, value = pair.split(': ')
        # Convert the key to lowercase and replace spaces with underscores
        key = key.lower().replace(' ', '_')
        # Handle specific data types
        if value.isdigit():
            value = str(value)
        elif value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif 'Duration' in key:
            value = int(value.split()[0])  # Extract the number from duration
        # Add the key-value pair to the dictionary
        event_data[key] = value

    return event_data


def extract_event_and_time(text, take_command=None, speak=None, model="gpt-4o-mini", recurrence=False):
    """
    Extract the event name, time components (year, month, day, hour, minute, period), duration, and whether the event is homework-related from the provided text.
    If any part of the time or duration is missing, prompt the user specifically for that part.
    If the recurrence parameter is True, also extract recurrence information.

    Returns:
    - event_name (str): The extracted event name.
    - time_string (str): The combined time string (e.g., '2024-07-15 07:30 PM').
    - recurrence_info (str or None): The recurrence pattern if recurrence is True, else None.
    - duration (str): The duration of the event, default to 'TBD' if not specified.
    - is_homework (bool): Whether the event is homework-related.
    """
    from datetime import datetime
    import pytz

    user_timezone_str = get_location_timezone()
    if user_timezone_str:
        user_timezone = pytz.timezone(user_timezone_str)
    else:
        user_timezone = pytz.timezone('US/Central')

    # Get the current date and time in the user's time zone
    now = datetime.now(user_timezone)
    # Includes date, time, and timezone abbreviation
    date_string = now.strftime("%A, %Y-%m-%d %I:%M %p %Z")

    print(date_string)

    # Construct the recurrence part of the string
    recurrence_part = (
        ", Recurring: [recurrence]. Format the recurrence pattern exactly as 'weekly Weekday/weekly Weekday'. "
        "Ensure that each weekday is prefixed with 'weekly' and separated by a single '/' without any spaces. "
        "Do not use any other format for recurrence information."
        if recurrence else ""
    )


    # Base prompt for extracting event details
    prompt = (
        f"Today is {date_string}. Extract event details from this sentence: '{text}'.\n"
        "Always follow this exact format for the output: Event: [event], Year: [year], Month: [month], Day: [day], "
        f"Hour: [hour in 12-hour format], Minute: [minute (2 digits)], Period: [AM/PM], Duration: [duration], Homework: [homework]{recurrence_part}'.\n"
        "The 'Time' components must always be formatted numerically. So, the year, month, day, hour, minute (always 2 digits), and period (AM/PM) should output as numbers.\n"
        "For 'Homework', set it to 'True' only if the event requires preparation or is an assignment. Set it to 'False' for events that do not require extra work.\n"
        "Ensure the output strictly follows this format. Any deviation from the format or variation in language is incorrect.\n\n"
        "Here are some example inputs and expected outputs to guide you. You must strictly follow these examples:\n\n"
        "Input: 'Add a CHC meeting at 5:30pm next Wednesday.'\n"
        "Current Date: '2024-09-26 11:00 AM CDT.'\n"
        "Output: Event: CHC meeting, Year: 2024, Month: 10, Day: 2, Hour: 5, Minute: 30, Period: PM, Duration: TBD, Homework: False \n\n"
        "Input: 'Add a meeting tomorrow at 2pm.'\n"
        "Current Date: '2024-09-26 11:00 AM CDT.'\n"
        "Output: Event: meeting, Year: 2024, Month: 9, Day: 27, Hour: 2, Minute: 00, Period: PM, Duration: TBD, Homework: False \n\n"
        "Input: 'Meeting on October 28th at 3pm.'\n"
        "Current Date: '2024-09-26 11:00 AM CDT.'\n"
        "Output: Event: meeting, Year: 2024, Month: 10, Day: 28, Hour: 3, Minute: 00, Period: PM, Duration: TBD, Homework: False \n\n"
        "Input: 'Add a recurring yoga session every Monday at 6am.'\n"
        "Current Date: '2024-09-26 11:00 AM CDT.'\n"
        "Output: Event: yoga session, Year: 2024, Month: 9, Day: 30, Hour: 6, Minute: 00, Period: AM, Duration: TBD, Homework: False, Recurring: weekly Monday \n\n"
        "Input: 'Doctor's appointment on the 15th of October at 9:45am.'\n"
        "Current Date: '2024-09-26 11:00 AM CDT.'\n"
        "Output: Event: Doctor's appointment, Year: 2024, Month: 10, Day: 15, Hour: 9, Minute: 45, Period: AM, Duration: TBD, Homework: False \n\n"
        "Please follow the exact format for the given input. Any deviation will be considered incorrect."
    )

    messages = [
        {"role": "system", "content": "You are a highly intelligent assistant tasked with extracting event details from text. Make sure to always match the examples given. Follow the output format exactly as specified without any variation."},
        {"role": "user", "content": prompt}
    ]

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=150,
        temperature=0
    )

    extracted_info = response.choices[0].message.content.strip()

    response_object = (parse_event_string(extracted_info))
    print(response_object)

    # Initialize default values
    event_name = response_object.get('event', 'Unnamed Event')
    year = response_object.get('year', 2024)
    month = response_object.get('month', 1)
    day = response_object.get('day', 1)
    hour = response_object.get('hour', 12)
    minute = response_object.get('minute', 0)
    period = response_object.get('period', 'AM')
    duration = response_object.get('duration', 'TBD')
    is_homework = response_object.get('homework', False)
    recurrence_info = response_object.get('recurring', None)

    # Check for missing components and prompt the user for specifics
    if not recurrence:
        if year == "TBD":
            year = prompt_for_missing_info("year", take_command, speak, "2024")

        if month == "TBD":
            month = prompt_for_missing_info("month", take_command, speak)

        if day == "TBD":
            day = prompt_for_missing_info("day", take_command, speak)

    if hour == "TBD" or minute == "TBD" or period == "TBD":
        time_input = prompt_for_missing_info(
            "hour, minute, and period (e.g., '7:30 PM')", take_command, speak)
        parsed_time = extract_time_from_string(time_input, model)
        hour = parsed_time.get("hour", "12")
        minute = parsed_time.get("minute", "00")
        period = parsed_time.get("period", "AM").upper()

    # Combine into a time string with AM/PM
    if recurrence:
        time_string = f"{hour}:{minute} {period}" 
    else:
        time_string = f"{year}-{month}-{day} {hour}:{minute} {period}"

    return event_name, time_string, recurrence_info, duration, is_homework


def prompt_for_missing_info(missing_part, take_command, speak, default=None):
    """
    Prompt the user for missing date or time components.

    Parameters:
    - missing_part (str): The part of the date/time that is missing (e.g., 'year', 'month').
    - take_command (function): Function to take user input.
    - speak (function): Function to provide spoken feedback.
    - default (str): The default value to return if no input is provided.

    Returns:
    - str: The provided or default value for the missing part.
    """
    if speak:
        speak(f"Please specify the {missing_part}.")
    else:
        print(f"Please specify the {missing_part}.")

    input_value = take_command() if take_command else input(
        f"Enter the {missing_part}: ")

    return input_value.strip() or default


def extract_time_from_string(time_input, model="gpt-4o-mini"):
    prompt = (
        f"Extract the hour, minute, and period (AM/PM) from this time string: '{time_input}'. "
        "Format the response as 'Hour: [hour], Minute: [minute], Period: [AM/PM]'."
    )

    messages = [
        {"role": "system", "content": "You are a highly intelligent assistant tasked with extracting time details from text."},
        {"role": "user", "content": prompt}
    ]

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=50,
        temperature=0
    )

    extracted_info = response.choices[0].message.content.strip()
    hour = None
    minute = None
    period = None

    if "Hour:" in extracted_info and "Minute:" in extracted_info and "Period:" in extracted_info:
        hour = extracted_info.split("Hour:")[1].split(",")[0].strip()
        minute = extracted_info.split("Minute:")[1].split(",")[0].strip()
        period = extracted_info.split("Period:")[1].strip()

    return {"hour": hour, "minute": minute, "period": period}


def schedule_retriever_interpreter(text, take_command=None, speak=None, model="gpt-4o-mini"):
    """
    Extract either the event name or the time from the provided text using GPT.
    This function handles various time formats (e.g., 'tomorrow', 'December 25th', 'a week from now').

    Returns:
    - event_name (str): The extracted event name, if present.
    - event_time (str): The extracted time component, if present.
    """
    from datetime import datetime

    # Get today's date for reference in the prompt
    today = datetime.today().strftime("%Y-%m-%d")

    prompt = (
        f"Today is {today}. Analyze the following sentence: '{text}'. "
        "If it contains an event name, respond with 'Event: [event name]'. "
        "If it contains a time expression, respond with 'Time: [time]'. "
        "For any time expressions, convert them to the format 'YYYY-M-D' (e.g., '2024-8-29') if they refer to a specific date. "
        "Be aware of indirect ways of asking for time, such as 'What's on my schedule today?' or 'What's on my agenda today?'—these are actually asking for a time, not an event. "
        "Only provide one of these two, whichever is mentioned in the sentence, and keep the response brief."
    )

    messages = [
        {"role": "system", "content": "You are a concise assistant tasked with extracting either the event name or time from text."},
        {"role": "user", "content": prompt}
    ]

    # Make the call to the GPT model to extract the information
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=50,  # Reduced token limit to save costs and enforce brevity
        temperature=0
    )

    # Get the extracted response from the model
    extracted_info = response.choices[0].message.content.strip()

    # Parse the extracted info to retrieve the event name or time
    event_name = None
    event_time = None

    # Improved parsing logic to find event name or time in the model's response
    if extracted_info.startswith("Event:"):
        event_name = extracted_info.split("Event:")[1].strip()
    elif extracted_info.startswith("Time:"):
        event_time = extracted_info.split("Time:")[1].strip()

    return event_name, event_time
