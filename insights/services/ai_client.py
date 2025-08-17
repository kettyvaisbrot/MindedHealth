import requests

def get_ai_insight(prompt):
    try:
        response = requests.post("http://localhost:8001/generate-insight/", json={"prompt": prompt})
        if response.status_code == 200:
            return response.json().get("insight", "")
        return f"AI service error: {response.status_code} {response.text}"
    except Exception as e:
        return f"Failed to contact AI service: {str(e)}"
