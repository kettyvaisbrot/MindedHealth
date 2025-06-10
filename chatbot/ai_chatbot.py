import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_ai_response(user_input):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_input,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].text.strip()

    except Exception as e:
        return f"Error: {str(e)}"
