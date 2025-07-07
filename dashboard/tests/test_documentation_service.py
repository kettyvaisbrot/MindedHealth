import pytest
from unittest.mock import patch, Mock
from dashboard.services.documentation_service import fetch_documentation_for_date
from requests.exceptions import RequestException

@pytest.mark.parametrize("date", ["2025-07-01", "2025-07-02"])
@patch("dashboard.services.documentation_service.requests.get")
def test_fetch_documentation_success(mock_get, date):
    mock_response = Mock()
    expected_data = {"some": "data"}
    mock_response.json.return_value = expected_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_documentation_for_date(date)

    mock_get.assert_called_once_with(f"http://localhost:8000/daily-documentation/{date}/", timeout=5)
    assert result == expected_data

@patch("dashboard.services.documentation_service.requests.get")
def test_fetch_documentation_request_exception(mock_get):
    mock_get.side_effect = RequestException("Connection error")

    result = fetch_documentation_for_date("2025-07-01")

    assert result == {}
