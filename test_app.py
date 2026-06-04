import json

import pytest

from app import create_app
import fetcher


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    path = tmp_path / "cache.json"
    monkeypatch.setattr(fetcher, "CACHE_PATH", path)
    return path


@pytest.fixture
def client(cache_file):
    app = create_app(enable_scheduler=False)
    app.config["TESTING"] = True
    return app.test_client()


def _write_store(path, entry, active_key="san francisco"):
    store = {
        "active_key": active_key,
        "entries": {active_key: entry},
    }
    path.write_text(json.dumps(store), encoding="utf-8")


def test_index_ok(client, cache_file):
    _write_store(
        cache_file,
        {
            "status": "ok",
            "query": "San Francisco",
            "city": "San Francisco, California, United States",
            "temperature_c": 18.2,
            "wind_speed_kmh": 12.5,
            "description": "Partly cloudy",
            "fetched_at": "2026-06-04T12:00:00+00:00",
            "error": None,
        },
    )
    response = client.get("/")
    assert response.status_code == 200
    assert b"San Francisco" in response.data
    assert b"app.js" in response.data


def test_index_error(client, cache_file):
    _write_store(
        cache_file,
        {
            "status": "error",
            "error": "Weather service unavailable",
        },
        active_key="error",
    )
    response = client.get("/")
    assert response.status_code == 503
    assert b"Weather unavailable" in response.data


def test_api_refresh_from_cache(client, cache_file):
    _write_store(
        cache_file,
        {
            "status": "ok",
            "query": "London",
            "city": "London, England",
            "temperature_c": 12.0,
            "wind_speed_kmh": 5.0,
            "description": "Cloudy",
            "fetched_at": "2099-01-01T00:00:00+00:00",
            "error": None,
        },
        active_key="london",
    )
    response = client.post(
        "/api/refresh",
        json={"city": "London"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["from_cache"] is True


def test_api_refresh_error_json(client, cache_file, monkeypatch):
    monkeypatch.setattr(
        fetcher,
        "refresh_weather",
        lambda city=None, force=False: {
            "status": "error",
            "error": "No location found",
            "from_cache": False,
        },
    )
    response = client.post("/api/refresh", json={"city": "Nowhereville"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "error"


def test_api_weather_found(client, cache_file):
    _write_store(
        cache_file,
        {
            "status": "ok",
            "query": "Paris",
            "city": "Paris, France",
            "temperature_c": 20.0,
            "fetched_at": "2026-06-04T12:00:00+00:00",
            "error": None,
        },
        active_key="paris",
    )
    response = client.get("/api/weather?city=Paris")
    assert response.status_code == 200
    assert response.get_json()["city"] == "Paris, France"


def test_api_weather_not_found(client, cache_file):
    cache_file.write_text(
        json.dumps({"active_key": None, "entries": {}}),
        encoding="utf-8",
    )
    response = client.get("/api/weather?city=Atlantis")
    assert response.status_code == 404
