from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from what_interested_you.views import fetch_search_results
import os

class FetchSearchResultsIntegrationTest(TestCase):
    """Integration test: calls the real Google API if credentials are present."""

    def setUp(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cse_id = os.getenv("GOOGLE_SEARCH_CSE_ID")

    def test_fetch_search_results_returns_items(self):
        if not self.api_key or not self.cse_id:
            self.skipTest("Google API credentials not set")

        query = "mental health"
        results = fetch_search_results(query)

        self.assertIsInstance(results, list)

        if results:
            for item in results:
                self.assertIn("title", item)
                self.assertIn("snippet", item)


class SearchViewUnitTest(TestCase):
    """Unit tests for search_view logic with mocking"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("what_interested_you:search")

    @patch("what_interested_you.views.fetch_search_results")
    def test_search_view_returns_results(self, mock_fetch):
        mock_fetch.return_value = [
            {"title": "Mental Health Tips", "snippet": "Some useful advice"}
        ]

        response = self.client.get(self.url, {"q": "mental health", "interest": "tips"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mental Health Tips")

    @patch("what_interested_you.views.fetch_search_results")
    def test_search_view_no_query(self, mock_fetch):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "")
        mock_fetch.assert_not_called()

    @patch("what_interested_you.views.fetch_search_results")
    def test_search_view_filters_by_interest(self, mock_fetch):
        mock_fetch.return_value = [
            {"title": "Best Therapy Methods", "snippet": "Some description"},
            {"title": "Random Article", "snippet": "Nothing related"}
        ]

        response = self.client.get(self.url, {"q": "health", "interest": "treatments"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Best Therapy Methods")
        self.assertNotContains(response, "Random Article")
