import json

import pytest

from app import create_app
import favorites


@pytest.fixture
def favorites_file(tmp_path, monkeypatch):
    path = tmp_path / "favorites.json"
    monkeypatch.setattr(favorites, "FAVORITES_PATH", path)
    return path


@pytest.fixture
def client(tmp_path, monkeypatch):
    import fetcher

    monkeypatch.setattr(fetcher, "CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(favorites, "FAVORITES_PATH", tmp_path / "favorites.json")
    app = create_app(enable_scheduler=False)
    app.config["TESTING"] = True
    return app.test_client()


def test_load_favorites_missing_file(favorites_file):
    assert favorites.load_favorites() == {"favorites": []}


def test_add_and_list_favorite(favorites_file):
    result = favorites.add_favorite("London", label="London, England")
    assert len(result) == 1
    assert result[0]["key"] == "london"
    assert result[0]["query"] == "London"
    assert result[0]["label"] == "London, England"
    assert favorites.is_favorite("London")


def test_add_duplicate_moves_to_front(favorites_file):
    favorites.add_favorite("Paris", label="Paris, France")
    favorites.add_favorite("London", label="London, England")
    result = favorites.add_favorite("Paris", label="Paris, France")
    assert len(result) == 2
    assert result[0]["key"] == "paris"
    assert result[1]["key"] == "london"


def test_remove_favorite(favorites_file):
    favorites.add_favorite("London", label="London, England")
    removed = favorites.remove_favorite("london")
    assert removed == []
    assert not favorites.is_favorite("london")


def test_remove_favorite_not_found(favorites_file):
    assert favorites.remove_favorite("atlantis") is None


def test_api_favorites_get_empty(client):
    response = client.get("/api/favorites")
    assert response.status_code == 200
    assert response.get_json() == {"favorites": []}


def test_api_favorites_post_and_get(client):
    post = client.post(
        "/api/favorites",
        json={"query": "London", "label": "London, England"},
    )
    assert post.status_code == 200
    data = post.get_json()
    assert len(data["favorites"]) == 1
    assert data["favorites"][0]["key"] == "london"

    get = client.get("/api/favorites")
    assert get.status_code == 200
    assert len(get.get_json()["favorites"]) == 1


def test_api_favorites_post_empty_query(client):
    response = client.post("/api/favorites", json={"query": "  "})
    assert response.status_code == 400


def test_api_favorites_delete(client):
    client.post(
        "/api/favorites",
        json={"query": "Paris", "label": "Paris, France"},
    )
    response = client.delete("/api/favorites/paris")
    assert response.status_code == 200
    assert response.get_json()["favorites"] == []


def test_api_favorites_delete_not_found(client):
    response = client.delete("/api/favorites/atlantis")
    assert response.status_code == 404


def test_favorites_persisted_to_file(favorites_file):
    favorites.add_favorite("Tokyo", label="Tokyo, Japan")
    stored = json.loads(favorites_file.read_text(encoding="utf-8"))
    assert stored["favorites"][0]["key"] == "tokyo"
