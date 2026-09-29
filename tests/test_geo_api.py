import pytest
import requests

from dvf_elt.ingest.geo_api import fetch_commune, GeoApiError

class FakeResponseOK:
    status_code = 200
    def raise_for_status(self): pass
    def json(self): return {"nom": "Paris", "code": "75056"}

class FakeResponse404:
    status_code = 404
    def raise_for_status(self): pass
    def json(self): return {}


def test_succeeds_after_two_timeouts_then_ok(monkeypatch):
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise requests.Timeout("simulated timeout")
        return FakeResponseOK()

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda seconds: None)  # skip real waiting in tests

    result = fetch_commune("75056")

    assert result["nom"] == "Paris"
    assert calls["count"] == 3


def test_gives_up_after_max_retries(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError("simulated connection error")

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    with pytest.raises(GeoApiError):
        fetch_commune("75056", max_retries=3)


def test_404_fails_immediately_without_retry(monkeypatch):
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        return FakeResponse404()

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(GeoApiError):
        fetch_commune("00000")

    assert calls["count"] == 1  # only tried once, no retry on a 404