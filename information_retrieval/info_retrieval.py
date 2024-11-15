from ask_gpt import classify_intent
from information_retrieval.weather import get_weather
from system import get_db, time_zone, city, lat, lon, region, country
import re
import spacy
from sentence_transformers import SentenceTransformer, util
from ask_gpt import simple_ask_gpt  # Assuming you have a GPT API integration
from fuzzywuzzy import fuzz
import os
import certifi
import pytz
import datetime


# Set up SSL context using certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

# Initialize database connection
db = get_db()

# Define collections
interactions_collection = db['interactions']

# Load the models
nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')



# Load models
nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Function to perform fuzzy matching
def fuzzy_match(input_text, candidate_text):
    return fuzz.partial_ratio(input_text.lower(), candidate_text.lower())

# Function to extract keywords using spaCy's Named Entity Recognition and POS tagging
def extract_keywords_with_spacy(text):
    doc = nlp(text)
    keywords = set()

    # Extract Named Entities (like people, dates, etc.)
    for ent in doc.ents:
        keywords.add(ent.text)

    # Extract important Nouns and Verbs (for deeper understanding)
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN", "VERB"):
            keywords.add(token.lemma_)  # Use lemma to normalize word forms (e.g., "knew" -> "know")


    return list(keywords)

# Main function to get similar interactions based on the user's question
def get_similar_interactions(question, interaction_limit=None, use_gpt=False):
    # Extract keywords using spaCy
    key_phrases_spacy = extract_keywords_with_spacy(question)
    
    # Build a regex pattern to match any of the extracted keywords
    if key_phrases_spacy:
        regex_pattern = ".*" + ".*|.*".join(re.escape(phrase) for phrase in key_phrases_spacy) + ".*"
    else:
        # If no key phrases are found, use a broad query
        regex_pattern = ".*" + re.escape(question) + ".*"

    # Query the collection for interactions containing the key phrases
    query = {"user_input": {"$regex": regex_pattern, "$options": "i"}}
    similar_interactions = list(interactions_collection.find(query).sort("_id", -1).limit(interaction_limit)) if interaction_limit else list(interactions_collection.find(query).sort("_id", -1))
    
    # Use Sentence-BERT for semantic similarity scoring
    question_embedding = model.encode(question, convert_to_tensor=True)
    scored_interactions = []
    
    for interaction in similar_interactions:
        interaction_text = interaction['user_input']
        
        # Use fuzzy matching on the interaction text and question for names, locations, etc.
        fuzzy_score = fuzzy_match(question, interaction_text)
        
        # Also compute semantic similarity using Sentence-BERT
        interaction_embedding = model.encode(interaction_text, convert_to_tensor=True)
        semantic_similarity = util.pytorch_cos_sim(question_embedding, interaction_embedding).item()

        # If either fuzzy score or semantic similarity is above a threshold, consider it relevant
        if fuzzy_score > 70 or semantic_similarity >= 0.7:
            scored_interactions.append((interaction, fuzzy_score, semantic_similarity))

    # Sort by a combination of fuzzy score and semantic similarity
    scored_interactions.sort(key=lambda x: (x[1], x[2]), reverse=True)

    # If GPT is enabled, refine the results using GPT
    if use_gpt and scored_interactions:
        gpt_input = f"Analyze the following question: '{question}'. Based on the question, rank the relevance of these past interactions:\n"
        gpt_input += "\n".join(
            [f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]: User said: '{interaction['user_input']}', Assistant responded: '{interaction['response']}'"
             for interaction, _, _ in scored_interactions]
        )
        
        # Ask GPT for the most relevant interactions
        refined_results = simple_ask_gpt(gpt_input)
        return f"GPT Refined Similar Interactions: {refined_results}"

    # Format and return the final results
    if scored_interactions:
        return "Similar Interactions: " + "; ".join(
            [
                f"[{interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]: User said: '{interaction['user_input']}', Assistant responded: '{interaction['response']}' (Fuzzy Score: {fuzzy_score}, Semantic Similarity: {semantic_similarity:.2f})"
                for interaction, fuzzy_score, semantic_similarity in scored_interactions
            ]
        )
    
    return "No similar interactions found."

import ssl
import certifi
from googlesearch import search

# Use certifi's certificate bundle for HTTPS requests
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Google search function using custom SSL context
def google_search(query, num_results=5):
    search_results = []
    for url in search(query, num=num_results, stop=num_results, pause=2):
        search_results.append(url)
    return search_results

from datetime import datetime
import pytz

def get_current_time_in_timezone():
    try:
        user_tz = pytz.timezone(time_zone)
        current_time = datetime.now(user_tz).strftime('%Y-%m-%d %H:%M:%S')
        return current_time
    except Exception as e:
        print(f"An error occurred while getting time for timezone '{time_zone}': {e}")
        return None


# Function to ask GPT for a refined search query
def refine_search_query(user_input):

    # Get the current time in user's timezone
    current_time = get_current_time_in_timezone()

    # Construct the prompt with detailed context
    prompt = (
        f"Given the user's input '{user_input}', current time '{current_time}' in timezone '{time_zone}', "
        f"and location details (City: {city}, Region: {region}, Country: {country}), "
        f"suggest a more specific Google search query that takes this context into account."
        f"Only respond with the refined search query and nothing else."
    )
    print(prompt)

    # Call GPT to refine the search query based on the prompt
    refined_query = simple_ask_gpt(prompt)
    return refined_query


# Updated information finding function with query refinement
def handle_information_finding(user_input):
    """
    Classifies the user's input into an intent category and retrieves data if necessary.
    
    Parameters:
    - user_input (str): The input text to classify.
    
    Returns:
    - result (str): The result of the classification, e.g., the weather information or a message.
    """
    # Add 'google_search' to the available categories
    categories = ['weather', 'google_search']

    # Dynamically generate the context message based on the categories
    categories_str = ', '.join(categories)
    context_message = (
        f"You are an AI tasked with determining if a user's request requires real-time information "
        f"from external sources such as APIs. The available categories for external data are: {categories_str}. "
        f"If the request pertains to any event or information after September 2021 (your knowledge cutoff), "
        f"such as news, current events, or recent developments, categorize it as needing real-time information. "
        f"Classify the user's input into one of these categories, and if it fits, return the category name. "
        f"Otherwise, state that no external information is required."
    )


    # Call the classify_intent function to determine the intent
    intent = classify_intent(user_input, categories, context_message=context_message)

    # Check the classified intent and call the appropriate function
    if intent == 'weather':
        # Retrieve weather information using the imported get_weather function
        weather_info = get_weather()
        return weather_info
    elif intent == 'google_search':
        # Step 1: Refine the search query using GPT
        print(user_input)
        refined_query = refine_search_query(user_input)
        print(refined_query)
        
        # Step 2: Perform a Google search with the refined query
        search_results = google_search(refined_query)
        print(search_results)
        
        # Step 3: Summarize the search results using GPT
        search_prompt = f"Summarize the information from these URLs:\n" + "\n".join(search_results)
        gpt_response = simple_ask_gpt(search_prompt)
        
        return gpt_response
    else:
        return "No external information is required for this request."
