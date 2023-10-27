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
serp_api_key = 'Add_your_api_here'

# Initialize the LangChain ChatAnthropic model
llm = ChatAnthropic()

# Update the path to your Knowledgebase folder
knowledgebase_folder = 'Knowledgebase'  # Replace with your folder path

# Combine text data from the Knowledgebase folder
knowledgebase_text = combine_text_from_folder(knowledgebase_folder)

# Clean and organize the combined information if necessary
knowledgebase_text = clean_and_organize(knowledgebase_text)

default_user_prompt = f"""

Add your prompt here

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
