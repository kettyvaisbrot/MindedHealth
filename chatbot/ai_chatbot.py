# chatbot/ai_chatbot.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_ai_response(user_input):
    try:
        # Send user input to OpenAI's GPT model for a response
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_input,
            max_tokens=150,
            temperature=0.7,
        )

        # Return the AI's response
        return response.choices[0].text.strip()

    except Exception as e:
        # Return error message in case of failure
        return f"Error: {str(e)}"
