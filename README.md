# cursor-weather-api

Warm-up weather dashboard by **harrisonhoggatt**. A small Flask app that caches current weather from [Open-Meteo](https://open-meteo.com/) and refreshes it on a background schedule.

## Project layout

```
cursor-weather-api/
├── app.py               # Flask routes only
├── fetcher.py           # Open-Meteo API calls and cache I/O
├── scheduler.py         # Background refresh (APScheduler)
├── data/
│   └── cache.json       # Per-city server cache
├── templates/
│   ├── index.html
│   └── _error.html
├── static/
│   ├── style.css
│   └── app.js           # In-page search + browser cache
├── .cursor/rules/       # Cursor agent rules
├── .env
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy or edit `.env` as needed:

```
DEFAULT_CITY=San Francisco
REFRESH_INTERVAL_MINUTES=15
CACHE_TTL_MINUTES=15
FLASK_DEBUG=1
```

## Run

```bash
flask --app "app:create_app()" run
```

Open http://127.0.0.1:5000/ in Chrome or Safari (Cursor’s built-in browser may show a blank page).

The scheduler fetches the default city on startup and every `REFRESH_INTERVAL_MINUTES`. Use the **Search** form to look up another city without a full page reload.

## Caching (rate-limit friendly)

**Server cache** (`data/cache.json`): stores multiple cities by normalized search key. Repeat lookups within `CACHE_TTL_MINUTES` skip Open-Meteo calls. Check **Force refresh** to bypass TTL. On each refresh (scheduler every `REFRESH_INTERVAL_MINUTES`, manual search, or API call), entries older than `CACHE_TTL_MINUTES` are **removed** from the file—only fresh cities are kept.

**Browser cache** (`localStorage`): mirrors successful lookups for the same TTL so re-searching a city in one session can avoid even calling `/api/refresh`. Stale browser entries are pruned after each API response.

**Last updated** is shown in your browser's local timezone (cache still stores UTC).

## JSON API

| Endpoint | Description |
|----------|-------------|
| `POST /api/refresh` | Body: `{"city": "London", "force": false}`. Returns weather JSON with `from_cache` boolean. Always HTTP 200; errors use `status: "error"`. |
| `GET /api/weather?city=London` | Read-only cached entry; 404 if missing. |

`POST /refresh` remains a no-JavaScript fallback (form POST + redirect).

## Tests

```bash
pytest
```

## Data source

Geocoding and forecast data from [Open-Meteo](https://open-meteo.com/). No API key required.
