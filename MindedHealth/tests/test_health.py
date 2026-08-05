import pytest
from django.test import Client


@pytest.mark.django_db
def test_healthz_returns_ok_when_db_and_redis_are_up():
    response = Client().get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_healthz_returns_503_when_redis_is_down(monkeypatch):
    from django.core.cache import cache

    def broken_set(*args, **kwargs):
        raise ConnectionError("redis unreachable")

    monkeypatch.setattr(cache, "set", broken_set)
    response = Client().get("/healthz/")
    assert response.status_code == 503
    assert response.json()["component"] == "redis"
