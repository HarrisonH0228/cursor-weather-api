const STORAGE_KEY = "weather_city_cache_v1";

function cacheKey(city) {
  return city.trim().toLowerCase();
}

function ttlMinutes() {
  const raw = document.body.dataset.cacheTtlMinutes;
  return parseInt(raw, 10) || 15;
}

function defaultCity() {
  return document.body.dataset.defaultCity || "San Francisco";
}

function getClientCache() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function setClientCache(key, data) {
  const store = getClientCache();
  store[key] = { data, stored_at: new Date().toISOString() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function pruneClientCache() {
  const store = getClientCache();
  let changed = false;
  for (const key of Object.keys(store)) {
    if (!isClientFresh(store[key])) {
      delete store[key];
      changed = true;
    }
  }
  if (changed) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  }
}

function isClientFresh(wrapper) {
  if (!wrapper || !wrapper.data || wrapper.data.status !== "ok") {
    return false;
  }
  const stored = new Date(wrapper.stored_at);
  if (Number.isNaN(stored.getTime())) {
    return false;
  }
  const ageMs = Date.now() - stored.getTime();
  return ageMs < ttlMinutes() * 60 * 1000;
}

function formatTemp(value) {
  if (value == null) return "—";
  return `${Number(value).toFixed(1)}°C`;
}

function formatWind(value) {
  if (value == null) return "";
  return `${Number(value).toFixed(1)} km/h`;
}

function setHint(message) {
  const el = document.getElementById("status-message");
  if (!el) return;
  if (message) {
    el.textContent = message;
    el.hidden = false;
    el.classList.add("status-hint");
    el.classList.remove("error-message");
  } else {
    el.hidden = true;
    el.textContent = "";
  }
}

function renderWeather(data, hint) {
  const card = document.getElementById("weather-card");
  card.classList.remove("error");

  document.getElementById("city-name").textContent = data.city || data.query || "";
  document.getElementById("conditions").textContent = data.description || "";
  document.getElementById("conditions").classList.remove("error-message");
  document.getElementById("conditions").classList.add("conditions");

  document.getElementById("temperature").textContent = formatTemp(data.temperature_c);

  const windRow = document.getElementById("wind-row");
  const windEl = document.getElementById("wind");
  if (data.wind_speed_kmh != null) {
    windRow.hidden = false;
    windEl.textContent = formatWind(data.wind_speed_kmh);
  } else {
    windRow.hidden = true;
  }

  const metrics = document.getElementById("metrics");
  if (metrics) metrics.hidden = false;

  const updated = document.getElementById("updated");
  if (data.fetched_at) {
    updated.textContent = `Last updated ${data.fetched_at}`;
    updated.hidden = false;
  } else {
    updated.hidden = true;
  }

  document.title = `Weather — ${data.city || data.query || ""}`;
  setHint(hint || "");
}

function renderError(data, hint) {
  const card = document.getElementById("weather-card");
  card.classList.add("error");

  document.getElementById("city-name").textContent = "Weather unavailable";
  const conditions = document.getElementById("conditions");
  conditions.textContent = data.error || "Unable to load weather data.";
  conditions.classList.add("error-message");
  conditions.classList.remove("conditions");

  const metrics = document.getElementById("metrics");
  if (metrics) metrics.hidden = true;

  const updated = document.getElementById("updated");
  if (updated) updated.hidden = true;

  if (data.city || data.query) {
    setHint(hint || `Requested: ${data.city || data.query}`);
  } else {
    setHint(hint || "");
  }

  document.title = "Weather unavailable";
}

function setLoading(loading) {
  const card = document.getElementById("weather-card");
  const button = document.getElementById("search-button");
  if (loading) {
    card.classList.add("loading");
    button.disabled = true;
    button.textContent = "Loading…";
  } else {
    card.classList.remove("loading");
    button.disabled = false;
    button.textContent = card.classList.contains("error") ? "Retry" : "Search";
  }
}

async function fetchWeather(city, force) {
  const response = await fetch("/api/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city, force }),
  });
  return response.json();
}

function hintForResponse(data) {
  if (data.from_cache) {
    return "Loaded from cache (no API call).";
  }
  if (data.status === "ok") {
    return "Updated just now.";
  }
  return "";
}

async function handleSearch(event) {
  event.preventDefault();

  const input = document.getElementById("city");
  const force = document.getElementById("force").checked;
  const city = (input.value.trim() || defaultCity());
  const key = cacheKey(city);

  if (!force) {
    const clientEntry = getClientCache()[key];
    if (isClientFresh(clientEntry)) {
      const data = clientEntry.data;
      if (data.status === "ok") {
        renderWeather(data, "Loaded from browser cache.");
      } else {
        renderError(data);
      }
      return;
    }
  }

  setLoading(true);
  try {
    const data = await fetchWeather(city, force);
    const hint = hintForResponse(data);

    if (data.status === "ok") {
      renderWeather(data, hint);
      setClientCache(key, data);
      pruneClientCache();
    } else {
      renderError(data, hint);
      pruneClientCache();
    }
  } catch {
    renderError({ error: "Could not reach the server. Try again." });
  } finally {
    setLoading(false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("search-form");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});
