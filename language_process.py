
import re
import dateparser
from datetime import datetime
import spacy
from spacy.lang.en.stop_words import STOP_WORDS as stop_words
from spacy.matcher import Matcher


nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# Broader patterns for matching scheduling intents
patterns = [
    [{"LOWER": {"IN": ["schedule", "remind", "add", "set", "create", "remove", "delete", "cancel"]}}],
    [{"LOWER": {"IN": ["what", "when", "do"]}}, {"LOWER": {"IN": ["time", "schedule", "appointment", "event", "reminder"]}}],
]

# Add patterns to the matcher, with valid string IDs
for i, pattern in enumerate(patterns):
    matcher.add(f"SCHEDULE_PATTERN_{i+1}", [pattern])

def is_text_scheduler(user_input):
    doc = nlp(user_input.lower())
    matches = matcher(doc)
    
    print(f"User input: {user_input}")
    print(f"Entities recognized: {[ent.text for ent in doc.ents]}")
    
    if matches:
        for match_id, start, end in matches:
            span_text = doc[start:end].text
            # Instead of using the string method directly, handle potential KeyError
            try:
                intent = nlp.vocab.strings[match_id]
            except KeyError:
                print(f"Unknown match_id: {match_id}")
                continue

            print(f"Matched pattern: {intent}, Text: {span_text}")
            
            # Consider the context: look for entities or keywords nearby
            if any(ent.label_ in ["DATE", "TIME", "EVENT"] for ent in doc.ents):
                print(f"Detected intent: {intent}, Text: {span_text}")
                return True
            
            # Fallback: check if relevant scheduling-related keywords are in the input
            if any(keyword in user_input for keyword in ["schedule", "appointment", "event", "reminder", "meeting"]):
                print(f"Detected intent via fallback: {intent}, Text: {span_text}")
                return True
    
    print("No intent detected")
    return False



def extract_and_parse_time(user_input, take_command, speak, reprompt=False):
    # Define regex patterns for extracting time-related phrases
    time_patterns = [
        r'\bin \d+ (?:minutes|hours|days|weeks|months)\b',  # e.g., "in 15 minutes", "in 2 weeks"
        r'\bnoon\b',  # e.g., "noon tomorrow", "noon on Friday"
        r'\b\d{1,2}:\d{2}\s?(?:am|pm)\b',  # e.g., 4:30pm
        r'\b\d{1,2}\s?(?:am|pm)\b',         # e.g., 2pm
        r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # Weekdays
        r'\b(?:tomorrow|yesterday|next week|next month)\b',  # Relative times
        r'\bat midnight\b',  # e.g., "at midnight"
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th)?,?\s?\d{0,4}?\s?\d{1,2}:\d{2}\s?(?:am|pm)?\b',  # e.g., "December 31st", "December 31, 15:59 pm"
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th)?\b'  # e.g., "December 31st"
    ]
    
    # Combine all patterns into one regex
    combined_pattern = '|'.join(time_patterns)
    
    # Search for matches in the string
    matches = re.findall(combined_pattern, user_input)
    
    # Ensure date and time are correctly captured together
    if len(matches) > 1:
        # This captures cases like "December 31st at 11:59pm"
        time_expression = ' '.join(matches)
    else:
        time_expression = matches[0] if matches else user_input
    
    # Parse the extracted time expression using dateparser
    parsed_time = dateparser.parse(time_expression, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
    
    # If a valid time is parsed, return it in a consistent format
    if parsed_time and parsed_time > datetime.now():
        return parsed_time.strftime('%B %d, %Y %I:%M %p')
    else:
        if reprompt:
            # If parsing fails, prompt the user to clarify the time
            speak("I couldn't understand the time. Can you clarify?")
            clarified_input = take_command()
            # Recursively call the function with the clarified input
            return extract_and_parse_time(clarified_input, take_command, speak)
        else:
            return None


def parse_event(sentence, take_command = None, speak = None):
    event_string = sentence.lower()
    if("office hours" in event_string):
        return "office hours"
    elif("doctor t" in event_string):
        return "therapy"
    elif("final exam" in event_string):
        return "final exam"
    
    
    doc = nlp(sentence)
    event_tokens = []

    # Expanded time-related keywords to exclude
    time_related_keywords = {
        "morning", "evening", "night", "today", "tomorrow", "yesterday",
        "noon", "midnight", "next", "last", "at", "on", "this", "weekend", "friday",
        "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday", "in","time", "jarvis"
    }

    # Array of scheduling-related verbs to exclude from the event
    scheduling_verbs = {
        "mark", "down", "remind", "schedule", "remember", "set", "write", "put", "note", "add", "book",
        "plan", "arrange", "register", "log", "list", "reserve", "save", "appoint",
        "prepare", "remind", "assign", "prepare", "establish", "jot", "calendar",
        "inscribe", "scribe", "input", "input", "detail", "program", "map", "catalog", "reserve", "reminder" 
    }

    for token in doc:
        # Ignore numbers, dates, time-related entities, stop words, and scheduling verbs
        if token.text.isdigit() or token.ent_type_ in {"TIME", "DATE"} or token.text.lower() in stop_words:
            continue
        # Exclude scheduling verbs
        if token.text.lower() not in scheduling_verbs:
            event_tokens.append(token.text)

    # After extracting the tokens, remove any time-related keywords and any tokens containing "am" or "pm"
    filtered_event_tokens = [
        token for token in event_tokens
        if token.lower() not in time_related_keywords and "am" not in token.lower() and "pm" not in token.lower()
    ]

    # Combine event tokens into a readable event description
    event = " ".join(filtered_event_tokens).strip()

    # Ensure the event string does not end with a space or period
    event = event.rstrip(" .?")

    # If no event is detected, prompt the user to clarify
    if not event:
        if(take_command== None or speak == None):
            return "No event found"
        
        speak("I didn't catch the event. Can you tell me again?")
        event = take_command()
        return parse_event(event, take_command, speak)
    
    return event


