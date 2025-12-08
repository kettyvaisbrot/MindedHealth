from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

# Initialize OpenAI client (reads OPENAI_API_KEY automatically)
client = OpenAI()

app = FastAPI()

class PromptInput(BaseModel):
    prompt: str

@app.post("/generate-insight")
def generate_insight(data: PromptInput):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "You are a compassionate mental health assistant."},
                {"role": "user", "content": data.prompt},
            ],
            max_tokens=700,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return {"insight": content.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
