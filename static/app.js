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

function formatFetchedAt(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function setUpdatedText(iso, fallback) {
  const updated = document.getElementById("updated");
  if (!updated) return;
  if (iso) {
    updated.textContent = `Last updated ${formatFetchedAt(iso)}`;
    updated.dataset.fetchedAt = iso;
    updated.hidden = false;
  } else {
    updated.textContent = fallback || "Last updated: unavailable";
    updated.hidden = false;
    delete updated.dataset.fetchedAt;
  }
}

function formatInitialTimestamp() {
  const updated = document.getElementById("updated");
  if (!updated) return;
  const iso = updated.dataset.fetchedAt;
  if (iso) {
    setUpdatedText(iso);
  }
}

function setStaleAlert(message, visible) {
  const alert = document.getElementById("stale-alert");
  if (!alert) return;
  if (visible && message) {
    alert.textContent = message;
    alert.classList.remove("d-none");
  } else {
    alert.classList.add("d-none");
  }
}

function setHint(message) {
  const el = document.getElementById("status-message");
  if (!el) return;
  if (message) {
    el.textContent = message;
    el.hidden = false;
  } else {
    el.hidden = true;
    el.textContent = "";
  }
}

function renderWeather(data, hint) {
  const card = document.getElementById("weather-card");
  card.classList.remove("border-danger");

  document.getElementById("city-name").textContent = data.city || data.query || "";
  const conditions = document.getElementById("conditions");
  conditions.textContent = data.description || "";
  conditions.classList.remove("text-danger");

  document.getElementById("temperature").textContent = formatTemp(data.temperature_c);

  const windRow = document.getElementById("wind-row");
  const windEl = document.getElementById("wind");
  if (data.wind_speed_kmh != null) {
    windRow.classList.remove("d-none");
    windEl.textContent = formatWind(data.wind_speed_kmh);
  } else if (windRow) {
    windRow.classList.add("d-none");
  }

  const metrics = document.getElementById("metrics");
  if (metrics) metrics.classList.remove("d-none");

  setUpdatedText(data.fetched_at);
  setStaleAlert(
    data.warning || (data.stale ? "Showing cached data; live refresh unavailable." : ""),
    Boolean(data.stale)
  );

  document.title = `Weather — ${data.city || data.query || ""}`;
  setHint(hint || "");
}

function renderError(data, hint) {
  if (data.status === "ok" || (data.stale && data.temperature_c != null)) {
    renderWeather(data, hint || data.warning);
    return;
  }

  const card = document.getElementById("weather-card");
  card.classList.add("border-danger");

  document.getElementById("city-name").textContent = "Weather unavailable";
  const conditions = document.getElementById("conditions");
  conditions.textContent = data.error || "Unable to load weather data.";

  const metrics = document.getElementById("metrics");
  if (metrics) metrics.classList.add("d-none");

  setStaleAlert(null, false);
  setUpdatedText(data.fetched_at, "Last updated: unavailable");

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
    button.textContent = card.classList.contains("border-danger") ? "Retry" : "Search";
  }
}

async function fetchWeather(city, force) {
  const response = await fetch("/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city, force }),
  });
  return response.json();
}

function hintForResponse(data) {
  if (data.stale) {
    return data.warning || "Showing cached data (API unavailable).";
  }
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
  const city = input.value.trim() || defaultCity();
  const key = cacheKey(city);

  if (!force) {
    const clientEntry = getClientCache()[key];
    if (isClientFresh(clientEntry)) {
      const data = clientEntry.data;
      if (data.status === "ok" || data.stale) {
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
  formatInitialTimestamp();
  const form = document.getElementById("search-form");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});
