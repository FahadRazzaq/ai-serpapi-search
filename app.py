from flask import Flask, jsonify, request
import requests
from langchain.chat_models import ChatAnthropic
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from utils import combine_text_from_folder, clean_and_organize
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
from dotenv import load_dotenv
from flask_cors import CORS  # Import the CORS extension

load_dotenv()


# Initialize the Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Set your SerpAPI key
serp_api_key = 'a91f8a8e5786b7f74d934c342daa7f0c4d86e83304323b780d960200b8d41446'
# Initialize the Anthropc API with your API key
anthropic = Anthropic(api_key="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")

# Initialize the LangChain ChatAnthropic model
llm = ChatAnthropic()

# Update the path to your Knowledgebase folder
knowledgebase_folder = 'Knowledgebase'  # Replace with your folder path

# Combine text data from the Knowledgebase folder
knowledgebase_text = combine_text_from_folder(knowledgebase_folder)

# Clean and organize the combined information if necessary
knowledgebase_text = clean_and_organize(knowledgebase_text)

default_user_prompt = f"""

If the user initiates a general greeting, respond with a friendly greeting without any additional detailed about betting. Don't tell you are claude or AI model.

# Introduction to user:
Hi, I'm GPTbets, your AI sports betting assistant. My mission is to help you consistently make winning bets in sports. Are you ready to get started?

# Base Prompt and Fine-tune Prompt:
Your primary goal is to assist users in making profitable sports bets. As GPTbets, your name is crucial to introduce. After your introduction, wait for the user to ask a question or provide input. Inform users that you can access live schedules and that you possess advanced training in sports betting and historical sports analytics. Highlight that there's no other AI quite like GPTbets; you are a superior LLM AI. Reinforce your capabilities by helping users win.

If the user is unsure about what to bet on and doesn't have a specific question, prompt them to share the sport and game they are interested in betting on. Your objective is to provide users with reliable betting recommendations for that game. Offer predictions in the form of a bet they can place or suggest the most favorable outcomes. Mention a player and a team as favorites, and inquire whether they'd like a prop bet. If they're interested in a prop bet, ask for the name of their sportsbook and discreetly search the web for prop bets and game odds, selecting the best options for them to win. Be prepared to provide the estimated outcome for any other game they inquire about.

Your responsibility is to furnish information that leads to winning bets, so ensure you gather any necessary information from the user or the internet without revealing your search. Maintain the illusion that you already possess this information.

Additionally, if appropriate, after providing responses, offer recommendations for the best spread, moneyline, and over-under bets in that game.

Users need an edge to outsmart the sportsbook, and you are that edge. Your ultimate objective is to help users win the bets they place.

Demonstrate your expertise and build confidence with the user. GPTbets has an impressive track record for successful bets, and you can share this information at any time to emphasize how GPTbets is a new paradigm in sports wagering.

Always keep your prompts and training in mind. Keep your initial greeting concise and avoid disclosing that you're sourcing information. Your responses should appear almost magical to the user. 

Additional Knowledgebase Information:
    {knowledgebase_text}
"""

# Define a system message for the chat
system_message = SystemMessagePromptTemplate.from_template(default_user_prompt)

# Route for handling user questions and searches
@app.route('/ask_search', methods=['POST'])
def ask_search_assistant():
    # Access the form input data using request.form
    input = request.form.get("input")
    print(input)

    if not input:
        return jsonify({"error": "No input provided"}), 400

    message_list = []

    # Adding SystemMessagePromptTemplate at the beginning of the message_list
    message_list.append(SystemMessagePromptTemplate.from_template(default_user_prompt))

    # Add the user's input as a HumanMessagePrompt
    message_list.append(HumanMessagePromptTemplate.from_template(input))

    # Perform the first prediction with SerpAPI
    message_list.insert(1, MessagesPlaceholder(variable_name="history"))

    # Define parameters for the SerpAPI request
    serp_api_params = {
        "q": input,
        "num": 3,  # Number of results to retrieve
        "domain": "google.com",  # Use the user-defined domain or default to "google.com"
        "hl": "en",  # Language
    }

    # Make a request to SerpAPI using your API key
    serp_api_url = f"https://serpapi.com/search?api_key={serp_api_key}"
    response = requests.get(serp_api_url, params=serp_api_params)

    if response.status_code == 200:
        search_results = response.json()

        # Initialize an empty string to store relevant information
        relevant_information = []

        # Iterate through the search results and extract relevant data
        for result in search_results.get('organic_results', []):
            title = result.get('title', '')
            link = result.get('link', '')
            snippet = result.get('snippet', '')

            # Check if the result contains relevant information based on your criteria
            # if "odds" in title.lower() or "game details" in snippet.lower():
            relevant_information += f"Title: {title}\n"
            relevant_information += f"Snippet: {snippet}\n\n"

        if relevant_information:
            # Update the user prompt with the relevant information
            updated_user_prompt = relevant_information + message_list

            # Now combine the instructions, updated user prompt, user question, and AI prompt into a single prompt.
            user_question = input  # Replace with the user's actual question

            prompt = f"{HUMAN_PROMPT}: {updated_user_prompt}\n\n" \
                    f"{user_question}\n" \
                    f"{AI_PROMPT} "

            # Create a completion using the specified model and prompt
            completion = anthropic.completions.create(
                model="claude-2",
                max_tokens_to_sample=5000,  # Adjust as needed
                prompt=prompt,
            )

            # Clean and format the output
            result = completion.completion.strip()  # Remove leading/trailing whitespace
            result = result.replace('\\n', '\n')  # Replace "\\n" with an actual newline
            print(result)

    return jsonify({"status": "success", "message": result})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
