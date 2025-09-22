from django.shortcuts import render
import requests
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os


lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

synonyms = {
    'treatments': ['treatment', 'therapy', 'medication', 'intervention', 'medications'],
    'symptoms': ['symptom', 'sign', 'indication', 'manifestation'],
    'tips': ['tip', 'advice', 'suggestion', 'recommendation']
}


def fetch_search_results(query):

    GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_CSE_ID = os.getenv('GOOGLE_SEARCH_CSE_ID')
    url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_CSE_ID}'

    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        return []

def search_view(request):
    query = request.GET.get('q', '')
    interest = request.GET.get('interest', '')
    results = []

    if query:
        results = fetch_search_results(query)
        if interest:
            interest_synonyms = synonyms.get(interest.lower(), [interest.lower()])
            filtered_results = []

            for result in results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                title_tokens = [lemmatizer.lemmatize(word) for word in word_tokenize(title) if word not in stop_words]
                snippet_tokens = [lemmatizer.lemmatize(word) for word in word_tokenize(snippet) if word not in stop_words]
                if any(synonym in title_tokens or synonym in snippet_tokens for synonym in interest_synonyms):
                    filtered_results.append(result)

            results = filtered_results

    context = {
        'results': results,
        'query': query,
        'interest': interest
    }
    return render(request, 'search_results.html', context)
