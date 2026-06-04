import json

import pytest
import responses

import fetcher


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    path = tmp_path / "cache.json"
    monkeypatch.setattr(fetcher, "CACHE_PATH", path)
    return path


def _mock_weather_apis():
    responses.add(
        responses.GET,
        fetcher.GEOCODING_URL,
        json={
            "results": [
                {
                    "name": "San Francisco",
                    "latitude": 37.77,
                    "longitude": -122.42,
                    "admin1": "California",
                    "country": "United States",
                }
            ]
        },
    )
    responses.add(
        responses.GET,
        fetcher.FORECAST_URL,
        json={
            "current": {
                "temperature_2m": 18.2,
                "weather_code": 2,
                "wind_speed_10m": 12.5,
            }
        },
    )


@responses.activate
def test_refresh_weather_success(cache_file):
    _mock_weather_apis()

    result = fetcher.refresh_weather("San Francisco")

    assert result["status"] == "ok"
    assert result["temperature_c"] == 18.2
    assert result["description"] == "Partly cloudy"
    assert result["error"] is None
    assert result["from_cache"] is False

    cached = json.loads(cache_file.read_text())
    entry = cached["entries"]["san francisco"]
    assert entry["status"] == "ok"
    assert "San Francisco" in entry["city"]
    assert cached["active_key"] == "san francisco"


@responses.activate
def test_refresh_skips_api_when_fresh(cache_file):
    _mock_weather_apis()
    fetcher.refresh_weather("San Francisco")
    assert len(responses.calls) == 2

    result = fetcher.refresh_weather("San Francisco")
    assert len(responses.calls) == 2
    assert result["from_cache"] is True
    assert result["status"] == "ok"


@responses.activate
def test_refresh_force_bypasses_ttl(cache_file):
    _mock_weather_apis()
    fetcher.refresh_weather("San Francisco")
    assert len(responses.calls) == 2

    fetcher.refresh_weather("San Francisco", force=True)
    assert len(responses.calls) == 4


@responses.activate
def test_error_entry_not_served_as_fresh(cache_file):
    responses.add(
        responses.GET,
        fetcher.GEOCODING_URL,
        json={"results": []},
    )
    fetcher.refresh_weather("Nowhereville")
    assert len(responses.calls) == 1

    responses.add(
        responses.GET,
        fetcher.GEOCODING_URL,
        json={"results": []},
    )
    result = fetcher.refresh_weather("Nowhereville")
    assert len(responses.calls) == 2
    assert result["status"] == "error"


@responses.activate
def test_refresh_weather_geocode_not_found(cache_file):
    responses.add(
        responses.GET,
        fetcher.GEOCODING_URL,
        json={"results": []},
    )

    result = fetcher.refresh_weather("Nowhereville")

    assert result["status"] == "error"
    assert "No location found" in result["error"]


def test_load_cache_missing_file(cache_file):
    assert fetcher.load_cache() == {"active_key": None, "entries": {}}


def test_load_cache_invalid_json(cache_file):
    cache_file.write_text("not json", encoding="utf-8")
    assert fetcher.load_cache() == {"active_key": None, "entries": {}}


def test_migrate_legacy_cache(cache_file):
    legacy = {
        "status": "ok",
        "city": "San Francisco, California, United States",
        "temperature_c": 16.0,
        "fetched_at": "2026-06-04T12:00:00+00:00",
        "error": None,
    }
    cache_file.write_text(json.dumps(legacy), encoding="utf-8")
    store = fetcher.load_cache()
    assert "entries" in store
    assert "san francisco" in store["active_key"]


def test_get_cached_weather_by_city(cache_file):
    store = {
        "active_key": "london",
        "entries": {
            "london": {"status": "ok", "city": "London", "query": "London"},
            "paris": {"status": "ok", "city": "Paris", "query": "Paris"},
        },
    }
    cache_file.write_text(json.dumps(store), encoding="utf-8")
    assert fetcher.get_cached_weather("Paris")["city"] == "Paris"
    assert fetcher.get_cached_weather()["city"] == "London"
