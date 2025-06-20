import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def get_ai_insight(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a compassionate mental health assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Something went wrong while generating insights. ({str(e)})"
