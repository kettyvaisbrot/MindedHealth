# utils.py

import requests

def fetch_search_results(query):
    api_key = 'AIzaSyDlMEso53m-NHo-3A4VM3BQKMV_5u1Rgzs'
    cse_id = '046ede44ce9e04a66'
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q={query}"

    response = requests.get(url)
    results = response.json().get('items', [])
    return results


def get_info_for_choice(query, choice):
    combined_query = f"{query} {choice}"
    refined_results = fetch_search_results(combined_query)
    return refined_results