# cursor-weather-api

Warm-up weather dashboard by **harrisonhoggatt**. Flask app with Bootstrap 5 UI, Open-Meteo data, file cache, and scheduled background refresh.

## Project layout

```
cursor-weather-api/
├── app.py               # Flask routes only
├── fetcher.py           # Open-Meteo API calls and cache I/O
├── favorites.py         # Starred cities (data/favorites.json)
├── scheduler.py         # Background refresh (APScheduler)
├── data/cache.json
├── data/favorites.json
├── templates/
│   ├── base.html        # Bootstrap 5 layout
│   ├── index.html
│   └── _error.html
├── static/
│   ├── style.css
│   └── app.js           # fetch() to POST /search
├── .cursor/rules/       # Includes architecture.mdc
├── .env
├── .flaskenv
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Edit `.env` (Open-Meteo needs no API key):

```
DEFAULT_CITY=San Francisco
REFRESH_INTERVAL_MINUTES=15
CACHE_TTL_MINUTES=15
FLASK_DEBUG=1
```

## Run

```bash
flask run
```

Uses `.flaskenv` (`FLASK_APP=app`). Alternative: `flask --app "app:create_app()" run`.

Open http://127.0.0.1:5000/ in Chrome or Safari.

## Features (project-reqs)

- **Cache:** API data stored in `data/cache.json`
- **Bootstrap 5** dashboard reading from cache
- **Scheduler:** default city refreshed every 15 minutes (`force=True`, always hits API)
- **Search:** in-page `POST /search` via JavaScript (no full reload)
- **Favorites:** star cities; persisted in `data/favorites.json`; sidebar shows cached temp/conditions; click a favorite to load weather
- **API down:** returns stale cached weather + timestamp when prior data exists
- **Last updated:** always shown (local timezone in browser)
- **Errors:** `_error.html` for failures and unhandled exceptions (no stack traces)

## Caching

Manual search respects `CACHE_TTL_MINUTES` unless **Force refresh** is checked. Scheduler ignores TTL for `DEFAULT_CITY`. Stale entries are pruned from `cache.json` on writes.

## API

| Endpoint | Description |
|----------|-------------|
| `POST /search` | Primary AJAX search: `{"city": "London", "force": false}` |
| `POST /api/refresh` | Alias of `/search` |
| `GET /api/weather?city=` | Read-only cache lookup |
| `GET /api/favorites` | List starred cities |
| `GET /api/favorites/weather` | Favorites with cached weather (temp + description) |
| `POST /api/favorites` | Add favorite: `{"query": "London", "label": "..."}` |
| `DELETE /api/favorites/<key>` | Remove favorite by normalized key |

## Tests

```bash
pytest
```

## Data source

[Open-Meteo](https://open-meteo.com/) — no API key required.
