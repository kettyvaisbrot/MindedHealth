import openai  

def get_ai_chat_response(user_input: str) -> str:
    if not user_input:
        raise ValueError("User input is required")

    # In real code, call the model here (mocked for now)
    return generate_ai_response(user_input)

def generate_ai_response(user_input: str) -> str:
    # You can swap in actual OpenAI code here
    return f"AI response to: {user_input}"
