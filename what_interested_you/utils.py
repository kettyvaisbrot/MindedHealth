# utils.py

import requests

def fetch_search_results(query):
    GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_CSE_ID = os.getenv('GOOGLE_SEARCH_CSE_ID')
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_CSE_ID}&q={query}"

    response = requests.get(url)
    results = response.json().get('items', [])
    return results


def get_info_for_choice(query, choice):
    combined_query = f"{query} {choice}"
    refined_results = fetch_search_results(combined_query)
    return refined_results