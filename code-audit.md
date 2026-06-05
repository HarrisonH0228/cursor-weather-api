# Code Audit

## app.py

### _template_context(app: Flask) -> dict
1. What does this function do?
- It returns a dictionary with template values for cache ttl minutes as well as the default city to use when opening the site for the first time.
2. What does it take as input, and what does it return?
    i. app (its just flask)
    ii. it returns a dictionary with template/default values for the program
3. What happens if the input is wrong or missing?
- If app is missing or not Flask, it will crash on app.config
4. Is there a simpler way to write this?
- By dropping the helper and using a context processor, we won't need to use the app argument.

### create_app(enable_scheduler: bool = True) -> Flask:
1. What does this function do?
- It creates a Flask object and declares several config settings for it
2. What does it take as input, and what does it return?
    i. It takes a True enable_scheduler boolean to decide whether or not to run APScheduler to refresh the cache periodically
    ii. It returns a Flask object
3. What happens if the input is wrong or missing?
- If the input was false, it would just run the program without APScheduler, which is what it already does when running tests
- The input cannot be missing because it is already passed as true inside the argument.
4. Is there a simpler way to write this?
- No

### _search_handler():
1. What does this function do?
- Gets the data from the API using the requests library
2. What does it take as input, and what does it return?
    i. Nothing.
    ii. Returns the output of refresh_weather with city as the input.
3. What happens if the input is wrong or missing?
- Nothing different happens
4. Is there a simpler way to write this?
- In the current way the program is set up, no

### index():
1. What does this function do?
- Gets the weather display information and template context, then checks if the data is 'ok' then renders the template or an error page depending on if the data was ok
2. What does it take as input, and what does it return?
    i. no input
    ii. it returns the string returned by render_template
3. What happens if the input is wrong or missing?
no input
4. Is there a simpler way to write this?
no

### refresh():
1. What does this function do?
- Gets weather data about a city then 'forces' a refresh with refresh_weather
2. What does it take as input, and what does it return?
    i. no inpue
    ii. it returns a redirect response object to "index"
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- the function is just reusing the code from _search_handler so just recall it inside refresh() instead of writing it again

### search():
1. What does this function do?
- Calls _search_handler() then returns the result as a json
2. What does it take as input, and what does it return?
    i. no input
    ii. returns a json of the result from the search
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- you can put the value of the variable inside the return statement to make it one line

### api_refresh():
1. What does this function do?
- Calls _search_handler() then returns the results as a json, this also might just be checking if the search handler still works after an api refresh
2. What does it take as input, and what does it return?
    i. no input
    ii. returns a json of the result from the search
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- you can make it one line if you take out the variable

### api_weather():
1. What does this function do?
- Gets data for the city and checks if there is cached data for the city
2. What does it take as input, and what does it return?
    i. nothing
    ii. returns a json entry of the weather from that city
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- not really

### handle_http_exception():
1. What does this function do?
- this function handles 404 http errors, and renders the error page if it occurs
2. What does it take as input, and what does it return?
    i. e variable
    ii. returns an error message 
3. What happens if the input is wrong or missing?
- It can't be missing because Flask will call this function when an error occurs, it's not a function the user should call
4. Is there a simpler way to write this?
- not without removing the HTTPException handler

### handle_500(e):
1. What does this function do?
- Handles internal 500 server errors
2. What does it take as input, and what does it return?
    i. takes e as an input, but the user does not call this function
    ii. returns an error template page Flask can display
3. What happens if the input is wrong or missing?
- the input can't be missing because Flask will be the one calling the function
4. Is there a simpler way to write this?
- no

## fetcher.py

### _default_city() -> str:
1. What does this function do?
- returns the default city from the env
2. What does it take as input, and what does it return?
    i. none
    ii. returns the default city from the env (San Francisco)
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- NO

### _cache_ttl_minutes() -> int:
1. What does this function do?
- returns the default TTL minutes from the env
2. What does it take as input, and what does it return?
    i. none
    ii. returns the default TTL minutes from the env (15 min)
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- no its one line

### _cache_key(query: str) -> str:
1. What does this function do?
- returns the input query stripped in lowercase
2. What does it take as input, and what does it return?
    i. query string
    ii. returns it stripped of end spaces and in lowercase
3. What happens if the input is wrong or missing?
- it will likely error trying to run .strip() on a non-string or None type
4. Is there a simpler way to write this?
- no its one line

### _empty_store() -> dict:
1. What does this function do?
- returns an empty dictionary
2. What does it take as input, and what does it return?
    i. nothing
    ii. returns an empty dictionary with the label "active_key" and "entries"
3. What happens if the input is wrong or missing?
- nothing
4. Is there a simpler way to write this?
- no

### _migrate_legcay_cache(raw: dict) -> dict:
1. What does this function do?
- upgrades the old cache into the new cache when refreshing
2. What does it take as input, and what does it return?
    i. takes a dictionary as input
    ii. if dict is modern, it returns the dictionary, if it has old contents it returns a new dictionary
3. What happens if the input is wrong or missing?
- it wouldn't be able to operate on the dictionary if it's not there or not a dictionary, erroring
4. Is there a simpler way to write this?
- replacing if query not in entry entry[query] = query with entry.setdefault(query, query) makes it one line shorter

### _normalize_store(raw: dict) -> dict:
1. What does this function do?
- Normalizes the raw dictionary input into the function
2. What does it take as input, and what does it return?
    i. a raw dictionary to be normalized
    ii. returns an empty dictionary, the raw dictionary, or migrates the dictionary into the modern format
3. What happens if the input is wrong or missing?
- it would likely error because it's only checking for dictionaries
- if it's a None type it would return an empty dictionary i believe
4. Is there a simpler way to write this?
- no

### load_cache() -> dict:
1. What does this function do?
- It loads the cache and makes a new one if one doesn't exist already
2. What does it take as input, and what does it return?
    i. nothing
    ii. it can either return an empty upgraded cache dictionary, or it can return an old cache turned into an upgraded cache dictionary 
3. What happens if the input is wrong or missing?
- no input
4. Is there a simpler way to write this?
- not really

### save_cache(data: dict) -> None:
1. What does this function do?
- saves and/or creates the cache file and writes the data into the file
2. What does it take as input, and what does it return?
    i. it takes the cache dictionary as input
    ii. it returns nothing
3. What happens if the input is wrong or missing?
- save_cache does no validation on its input so it could error if you input something incorrectly into the function
4. Is there a simpler way to write this?
- not meaningfully

### _parse_fetched_at(value: str | None) -> datetime | None:
1. What does this function do?
- this function takes the time output by the program and converts it into the user's local timezone
2. What does it take as input, and what does it return?
    i. "value" the UTC time value at which the data was last fetched
    ii. It returns nothing if the value is missing/incorrect or if an error occurs, it returns the parsed time format if it can do the operation
3. What happens if the input is wrong or missing?
- If the input is wrong/missing it will return nothing and not error
4. Is there a simpler way to write this?
- no

### _is_fresh(entry: dict, ttl_minutes: int | None = None) -> bool:
1. What does this function do?
- checks if a cache entry is too old (≥15min)
2. What does it take as input, and what does it return?
    i. the cache dict and the ttl_minutes
    ii. a boolean 'False' if cache is too old or bad, and 'True' if the cache is still fresh
3. What happens if the input is wrong or missing?
- If the cache is invalid or bad then it will default to return False
4. Is there a simpler way to write this?
- you can use timedelta instead of seconds math, and you can move the timezone fix into _parse_fetched_at() instead, this would save 2 lines

### get_entry(city: str | None) -> dict | None:
1. What does this function do?
- gets the selected entry for a city
2. What does it take as input, and what does it return?
    i. it takes a city name as a string
    ii. it returns the desired entry, or nothing if it doesn't exist
3. What happens if the input is wrong or missing?
- If the input is empty, the function defaults to active_key, but if the input is a wrong type, it will crash eventually.
4. Is there a simpler way to write this?
- no

### get_cached_weather(city: str | None = None) -> dict:
1. What does this function do?
- looks for and gets a cached entry of weather in a city
2. What does it take as input, and what does it return?
    i. it takes a string or None as input
    ii. it returns either the data entry for the city or an empty dict
3. What happens if the input is wrong or missing?
- If the input is missing it will return an empty dict
4. Is there a simpler way to write this?
- no

### get_display_weather(city: str | None = None) -> dict:
1. What does this function do?
- Return weather suitable for the main UI
2. What does it take as input, and what does it return?
    i. city string or None
    ii. returns a dictionary
3. What happens if the input is wrong or missing?
- if city is missing active_key is used, incorrect inputs won't crash
4. Is there a simpler way to write this?
- merging get_entry() and load_cache() into one cache read would be more efficient

### _prune_stale_entries(store: dict, always_keep: str | None = None) -> dict:
1. What does this function do?
- Updates cache, getting rid of stale entries (older than 15min)
2. What does it take as input, and what does it return?
    i. store: dict, and always_keep: str
    ii. it returns a new dictionary which has the stale entries pruned from it
3. What happens if the input is wrong or missing?
- 
4. Is there a simpler way to write this?

### _error_entry(message: str, query)
1. What does this function do?
2. What does it take as input, and what does it return?
    i. 
    ii. 
3. What happens if the input is wrong or missing?
4. Is there a simpler way to write this?

### _persist_entry(store: dict, key: str, entry: dict) -> None:
1. What does this function do?
2. What does it take as input, and what does it return?
    i. 
    ii. 
3. What happens if the input is wrong or missing?
4. Is there a simpler way to write this?

### _response_with_meta(entry: dict, from_cache: bool) -> dict:

### _stale_response(existing: dict, warning: str) -> dict:

### _maybe_return_stale(existing: dict | None, warning: str) -> dict | None:

### _geocode(city: str) -> tuple[float, float, str]:

### _fetch_current(latitude: float, longitude: float) -> dict:

### _weather_description(code: int) -> str:

### refresh_weather(city: str | None = None, force: bool = False) -> dict:

## scheduler.py

### _refresh_interval_minutes() -> int:

### _scheduled_refresh() -> None:

### init_scheduler(app=None) -> BackgroundScheduler:

### shutdown_scheduler() -> None: