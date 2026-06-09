from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fetcher import _cache_key

logger = logging.getLogger(__name__)

FAVORITES_PATH = Path(__file__).parent / "data" / "favorites.json"


def _empty_store() -> dict:
    return {"favorites": []}


def load_favorites() -> dict:
    if not FAVORITES_PATH.exists():
        return _empty_store()
    try:
        with FAVORITES_PATH.open(encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict) or "favorites" not in raw:
            return _empty_store()
        if not isinstance(raw["favorites"], list):
            return _empty_store()
        return raw
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read favorites: %s", exc)
        return _empty_store()


def save_favorites(data: dict) -> None:
    FAVORITES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FAVORITES_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def list_favorites() -> list[dict]:
    return load_favorites().get("favorites", [])


def is_favorite(key: str) -> bool:
    normalized = _cache_key(key)
    return any(item.get("key") == normalized for item in list_favorites())


def add_favorite(query: str, label: str | None = None) -> list[dict]:
    query = query.strip()
    key = _cache_key(query)
    display = (label or query).strip() or query
    entry = {
        "key": key,
        "query": query,
        "label": display,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    store = load_favorites()
    favorites = [item for item in store.get("favorites", []) if item.get("key") != key]
    favorites.insert(0, entry)
    store["favorites"] = favorites
    save_favorites(store)
    return favorites


def remove_favorite(key: str) -> list[dict] | None:
    normalized = _cache_key(key)
    store = load_favorites()
    favorites = store.get("favorites", [])
    kept = [item for item in favorites if item.get("key") != normalized]
    if len(kept) == len(favorites):
        return None
    store["favorites"] = kept
    save_favorites(store)
    return kept
