import pytest
import requests

from dvf_elt.ingest.geo_api import fetch_all_communes, fetch_commune, GeoApiError

class FakeResponseOK:
    status_code = 200
    def __init__(self, data=None):
        self._data = data if data is not None else {"nom": "Paris", "code": "75056"}
    def raise_for_status(self): pass
    def json(self): return self._data

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


def test_fetch_all_communes_combines_communes_and_arrondissements(monkeypatch):
    calls = []

    def fake_get(url, params=None, **kwargs):
        calls.append((url, params))
        if params and params.get("type") == "arrondissement-municipal":
            return FakeResponseOK([{"code": "75101", "nom": "Paris 1er"}])
        return FakeResponseOK([{"code": "01001", "nom": "L'Abergement-Clémenciat"}])

    monkeypatch.setattr(requests, "get", fake_get)

    data = fetch_all_communes(include_arrondissements=True)
    assert len(data) == 2
    codes = {c["code"] for c in data}
    assert "01001" in codes
    assert "75101" in codes
    assert len(calls) == 2


def test_fetch_all_communes_retries_transient_error(monkeypatch):
    attempt = {"count": 0}

    def fake_get(url, params=None, **kwargs):
        attempt["count"] += 1
        if attempt["count"] == 1:
            raise requests.Timeout("timed out")
        return FakeResponseOK([{"code": "01001", "nom": "Commune 1"}])

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    data = fetch_all_communes(include_arrondissements=False)
    assert len(data) == 1
    assert attempt["count"] == 2