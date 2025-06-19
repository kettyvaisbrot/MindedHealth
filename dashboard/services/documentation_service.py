import datetime
import requests
from django.urls import reverse
from requests.exceptions import RequestException

def fetch_documentation_for_date(date):
    try:
        api_url = f"http://localhost:8000/daily-documentation/{date}/"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except RequestException:
        return {}
