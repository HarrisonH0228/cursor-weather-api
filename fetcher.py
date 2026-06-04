from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_PATH = Path(__file__).parent / "data" / "cache.json"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10

WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def _default_city() -> str:
    return os.getenv("DEFAULT_CITY", "San Francisco")


def _cache_ttl_minutes() -> int:
    return int(os.getenv("CACHE_TTL_MINUTES", "15"))


def _cache_key(query: str) -> str:
    return query.strip().lower()


def _empty_store() -> dict:
    return {"active_key": None, "entries": {}}


def _migrate_legacy_cache(raw: dict) -> dict:
    if "status" not in raw:
        return raw
    query = raw.get("city") or _default_city()
    key = _cache_key(query)
    entry = {k: v for k, v in raw.items() if k != "from_cache"}
    if "query" not in entry:
        entry["query"] = query
    return {"active_key": key, "entries": {key: entry}}


def _normalize_store(raw: dict) -> dict:
    if not raw:
        return _empty_store()
    if "entries" in raw:
        return raw
    return _migrate_legacy_cache(raw)


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return _empty_store()
    try:
        with CACHE_PATH.open(encoding="utf-8") as f:
            raw = json.load(f)
        return _normalize_store(raw)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read cache: %s", exc)
        return _empty_store()


def save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _parse_fetched_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_fresh(entry: dict, ttl_minutes: int | None = None) -> bool:
    if entry.get("status") != "ok":
        return False
    fetched_at = _parse_fetched_at(entry.get("fetched_at"))
    if fetched_at is None:
        return False
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    ttl = ttl_minutes if ttl_minutes is not None else _cache_ttl_minutes()
    age_seconds = (datetime.now(timezone.utc) - fetched_at).total_seconds()
    return age_seconds < ttl * 60


def get_entry(city: str | None) -> dict | None:
    store = load_cache()
    if not city:
        key = store.get("active_key")
    else:
        key = _cache_key(city)
    if not key:
        return None
    return store.get("entries", {}).get(key)


def get_cached_weather(city: str | None = None) -> dict:
    entry = get_entry(city)
    return entry if entry is not None else {}


def _prune_stale_entries(store: dict, always_keep: str | None = None) -> dict:
    entries = store.get("entries", {})
    before = len(entries)
    kept = {}
    for key, entry in entries.items():
        if key == always_keep or _is_fresh(entry):
            kept[key] = entry
    store["entries"] = kept
    if store.get("active_key") not in kept:
        if always_keep and always_keep in kept:
            store["active_key"] = always_keep
        else:
            store["active_key"] = next(iter(kept), None)
    pruned = before - len(kept)
    if pruned:
        logger.info("Pruned %s stale cache entr%s", pruned, "y" if pruned == 1 else "ies")
    return store


def _error_entry(message: str, query: str | None = None) -> dict:
    return {
        "status": "error",
        "query": query,
        "city": query,
        "latitude": None,
        "longitude": None,
        "temperature_c": None,
        "wind_speed_kmh": None,
        "description": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": message,
    }


def _persist_entry(store: dict, key: str, entry: dict) -> None:
    entry = {k: v for k, v in entry.items() if k != "from_cache"}
    store.setdefault("entries", {})[key] = entry
    store["active_key"] = key
    _prune_stale_entries(store, always_keep=key)
    save_cache(store)


def _response_with_meta(entry: dict, from_cache: bool) -> dict:
    result = dict(entry)
    result["from_cache"] = from_cache
    return result


def _geocode(city: str) -> tuple[float, float, str]:
    response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise ValueError(f"No location found for '{city}'")
    location = results[0]
    name = location.get("name", city)
    admin = location.get("admin1")
    country = location.get("country")
    parts = [name]
    if admin:
        parts.append(admin)
    if country:
        parts.append(country)
    display_name = ", ".join(parts)
    return location["latitude"], location["longitude"], display_name


def _fetch_current(latitude: float, longitude: float) -> dict:
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    current = response.json().get("current") or {}
    if "temperature_2m" not in current:
        raise ValueError("Forecast response missing current weather")
    return current


def _weather_description(code: int) -> str:
    return WMO_DESCRIPTIONS.get(code, "Unknown conditions")


def refresh_weather(city: str | None = None, force: bool = False) -> dict:
    target_city = (city or _default_city()).strip()
    if not target_city:
        entry = _error_entry("City name is required")
        return _response_with_meta(entry, from_cache=False)

    key = _cache_key(target_city)
    store = load_cache()
    existing = store.get("entries", {}).get(key)

    if not force and existing and _is_fresh(existing):
        store["active_key"] = key
        _prune_stale_entries(store, always_keep=key)
        save_cache(store)
        logger.info("Serving cached weather for %s", target_city)
        return _response_with_meta(existing, from_cache=True)

    try:
        latitude, longitude, display_name = _geocode(target_city)
        current = _fetch_current(latitude, longitude)
        weather_code = int(current.get("weather_code", 0))
        entry = {
            "status": "ok",
            "query": target_city,
            "city": display_name,
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": current["temperature_2m"],
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "description": _weather_description(weather_code),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
        _persist_entry(store, key, entry)
        logger.info("Weather cache updated for %s", display_name)
        return _response_with_meta(entry, from_cache=False)
    except requests.RequestException as exc:
        logger.error("Weather API request failed: %s", exc)
        entry = _error_entry(f"Weather service unavailable: {exc}", target_city)
    except (ValueError, KeyError) as exc:
        logger.error("Weather fetch failed: %s", exc)
        entry = _error_entry(str(exc), target_city)
    except Exception as exc:
        logger.error("Unexpected weather fetch error: %s", exc)
        entry = _error_entry(f"Unexpected error: {exc}", target_city)

    _persist_entry(store, key, entry)
    return _response_with_meta(entry, from_cache=False)
