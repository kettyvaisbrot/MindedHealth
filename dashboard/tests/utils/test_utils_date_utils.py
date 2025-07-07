import pytest
from dashboard.utils.date_utils import parse_date_from_str
from datetime import date


def test_valid_date_string():
    result = parse_date_from_str("2024-12-01")
    assert isinstance(result, date)
    assert result == date(2024, 12, 1)


def test_invalid_format_returns_none():
    assert parse_date_from_str("01-12-2024") is None
    assert parse_date_from_str("2024/12/01") is None
    assert parse_date_from_str("not-a-date") is None


def test_empty_string_returns_none():
    assert parse_date_from_str("") is None


def test_none_input_returns_none():
    assert parse_date_from_str(None) is None  # Optional: only if your app might pass None
