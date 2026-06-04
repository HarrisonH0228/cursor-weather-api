### What the app must do:

1. Fetch data from your API → store in `data/cache.json`
2. Serve a web page reading from cache — clean Bootstrap 5 layout
3. Refresh cache automatically every 15 minutes via APScheduler
4. Let the user search or filter without a full page reload (JavaScript `fetch()` to a `/search` route)
5. Handle errors gracefully — API down → show stale cache with timestamp, not a crash
6. Display a "last updated" timestamp at all times
7. Show a proper error page (`_error.html`) for unhandled exceptions — no raw stack traces

### Hard rules:

1. API keys in `.env` only. Hardcoded key = exercise doesn't count.
2. `fetcher.py` is separate from `app.py`. Routes do not contain API logic.
3. Use the AI terminal (Cmd+K) for all shell operations today.
4. Use `@docs` when asking about Flask or APScheduler APIs.
5. Update your `.cursor/rules/architecture.mdc` rule file whenever you make a structural decision.
6. App must run cleanly with `flask run` before you commit.