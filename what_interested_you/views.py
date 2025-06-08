from django.shortcuts import render
import requests
import nltk

nltk.download("punkt")  # Add this line to download the 'punkt' tokenizer model
nltk.download("wordnet")
nltk.download("omw-1.4")  # For extended WordNet support
nltk.download("stopwords")
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

# Define a comprehensive synonyms dictionary
synonyms = {
    "treatments": ["treatment", "therapy", "medication", "intervention", "medications"],
    "symptoms": ["symptom", "sign", "indication", "manifestation"],
    "tips": ["tip", "advice", "suggestion", "recommendation"],
}


def fetch_search_results(query):

    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_CSE_ID = os.getenv("GOOGLE_SEARCH_CSE_ID")
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_CSE_ID}"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        return []


def search_view(request):
    query = request.GET.get("q", "")
    interest = request.GET.get("interest", "")
    results = []

    if query:
        results = fetch_search_results(query)

        # Filter results based on user interest
        if interest:
            interest_synonyms = synonyms.get(interest.lower(), [interest.lower()])
            filtered_results = []

            for result in results:
                # Extract title and snippet from result
                title = result.get("title", "").lower()
                snippet = result.get("snippet", "").lower()

                # Lemmatize and tokenize title and snippet
                title_tokens = [
                    lemmatizer.lemmatize(word)
                    for word in word_tokenize(title)
                    if word not in stop_words
                ]
                snippet_tokens = [
                    lemmatizer.lemmatize(word)
                    for word in word_tokenize(snippet)
                    if word not in stop_words
                ]

                # Check for the presence of any synonym in the lemmatized tokens
                if any(
                    synonym in title_tokens or synonym in snippet_tokens
                    for synonym in interest_synonyms
                ):
                    filtered_results.append(result)

            results = filtered_results

    context = {"results": results, "query": query, "interest": interest}
    return render(request, "search_results.html", context)
