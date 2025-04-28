# chatbot/ai_chatbot.py
import openai
import os

# Set the OpenAI API key (you can load this from an environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure the key is set in your .env file

def generate_ai_response(user_input):
    try:
        # Send user input to OpenAI's GPT model for a response
        response = openai.Completion.create(
            engine="text-davinci-003",  # Choose the desired OpenAI model (e.g., GPT-3)
            prompt=user_input,          # The input from the user
            max_tokens=150,             # Limit the response length (you can adjust this)
            temperature=0.7,            # Adjust creativity of the response
        )

        # Return the AI's response
        return response.choices[0].text.strip()

    except Exception as e:
        # Return error message in case of failure
        return f"Error: {str(e)}"
