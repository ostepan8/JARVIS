from system import get_db
from datetime import datetime
from ask_gpt import ask_gpt, ask_json
import json
from bson import ObjectId
import re
# Initialize database connection
db = get_db()

# Define collections
interactions_collection = db['interactions']
user_collection = db['users']

def store_interaction(user_id, user_input, response, intent):
    """
    Store each interaction in the interactions collection.
    """
    interaction = {
        'user_id': user_id,
        'user_input': user_input,
        'response': response,
        'timestamp': datetime.now(),
        'intent': intent
    }
    interactions_collection.insert_one(interaction)



def make_serializable(data):
    """
    Convert any ObjectId instances in the data to strings for JSON serialization.
    """
    if isinstance(data, dict):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_serializable(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

def make_serializable(data):
    """
    Recursively convert any ObjectId instances in the data to strings for JSON serialization.
    """
    if isinstance(data, dict):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_serializable(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

def sanitize_json_response(response):
    """
    Sanitize the JSON response to ensure it can be properly parsed.
    """
    try:
        # Remove any Markdown-style code block delimiters and extra whitespace
        response = re.sub(r"```[a-zA-Z]*\n?", "", response).strip()
        return json.loads(response)
    except json.JSONDecodeError:
        # Additional sanitization steps
        response = response.replace("'", "\"")
        response = re.sub(r",\s*}", "}", response)
        response = re.sub(r",\s*]", "]", response)
        response = re.sub(r"\s+", " ", response).strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Failed to sanitize and parse response: {e}")
            return {}

def fetch_user_profile(user_id):
    """
    Fetch the user's profile from the database or initialize it if it doesn't exist.
    """
    user_profile = user_collection.find_one({'user_id': user_id})
    if not user_profile:
        user_profile = {'user_id': user_id, 'preferences': {}, 'habits': [], 'behavioral_patterns': {}}
    return user_profile

def generate_gpt_prompt(user_profile, user_input, response):
    """
    Generate a prompt for GPT to analyze and suggest updates to the user profile.
    """
    # Remove the '_id' field to reduce tokens
    user_profile.pop('_id', None)  # Safely remove '_id' if it exists

    serializable_profile = make_serializable(user_profile)
    user_name = user_profile.get('name', 'the user')
    gpt_prompt = (
        f"Update the user profile: {json.dumps(serializable_profile)}. "
        f"Based on the user's last input: '{user_input}' and your previous response: '{response}', suggest only factual updates about the user's personal background, preferences, or identity. "
        "Focus strictly on relevant and verifiable details about the user, such as their interests, personality, family, favorite foods, music tastes, hobbies, location, and other concrete personal attributes. "
        "Do not include information related to specific interactions or temporary details, such as scheduling, moods, or conversational history, as they are irrelevant for the long-term profile. "
        "Only provide updates that are general facts or consistent personal preferences. Do not make assumptions or add any speculative details. "
        "Return the updated profile in JSON format, or the unchanged profile if no updates are needed."
    )


    return gpt_prompt


def update_user_profile(user_id, profile_updates):
    """
    Update the user's profile in the database with the provided updates.
    """
    if profile_updates:
        # Fetch current profile
        user_profile = fetch_user_profile(user_id)

        # Apply updates to the profile
        for key, value in profile_updates.items():
            if key != "_id":
                user_profile[key] = value

        # Update the user profile in MongoDB
        user_collection.update_one({'user_id': user_id}, {'$set': user_profile}, upsert=True)

def analyze_and_update_profile(user_id, user_input, response):
    """
    Analyze the user's input and response to determine if the profile needs updating.
    """
    # Fetch user profile
    user_profile = fetch_user_profile(user_id)

    # Generate a prompt for GPT
    gpt_prompt = generate_gpt_prompt(user_profile,user_input, response)

    # Get suggestions for profile updates
    gpt_response = ask_json(gpt_prompt)
    

    # Sanitize and parse GPT response
    profile_updates = sanitize_json_response(gpt_response)

    # Update user profile in the database
    update_user_profile(user_id, profile_updates)


def find_similar_interactions(user_input, top_n=5):
    """
    Find similar past interactions using vector search or regex matching for efficient look-up.
    """
    # Here, you could implement a vector-based similarity search for efficiency
    # Example with regex matching (as a placeholder)
    pattern = re.compile(re.escape(user_input), re.IGNORECASE)
    similar_interactions = list(interactions_collection.find({'user_input': pattern}).limit(top_n))
    return similar_interactions
