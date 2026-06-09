const STORAGE_KEY = "weather_city_cache_v1";

let currentQuery = null;
let currentKey = null;
let favorites = [];

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

  currentQuery = data.query || data.city || null;
  currentKey = currentQuery ? cacheKey(currentQuery) : null;

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
  updateStarButton();
  loadFavoritesSidebar();
}

function isFavorited(key) {
  return favorites.some((item) => item.key === key);
}

function updateStarButton() {
  const button = document.getElementById("favorite-toggle");
  if (!button) return;

  if (!currentKey || !currentQuery) {
    button.hidden = true;
    return;
  }

  button.hidden = false;
  button.dataset.query = currentQuery;
  button.dataset.label = document.getElementById("city-name")?.textContent || currentQuery;

  const starred = isFavorited(currentKey);
  button.textContent = starred ? "★" : "☆";
  button.classList.toggle("btn-warning", starred);
  button.classList.toggle("btn-outline-warning", !starred);
  button.setAttribute("aria-label", starred ? "Remove from favorites" : "Add to favorites");
  button.title = starred ? "Remove from favorites" : "Add to favorites";
}

function renderFavoritesSidebar(items) {
  const list = document.getElementById("favorites-sidebar-list");
  const empty = document.getElementById("favorites-empty");
  if (!list) return;

  list.innerHTML = "";

  if (!items.length) {
    if (empty) empty.classList.remove("d-none");
    updateStarButton();
    return;
  }

  if (empty) empty.classList.add("d-none");

  for (const item of items) {
    const row = document.createElement("div");
    row.className =
      "list-group-item list-group-item-action favorites-sidebar-item d-flex align-items-center justify-content-between gap-2";
    if (item.key === currentKey) {
      row.classList.add("active");
    }
    row.setAttribute("role", "listitem");
    row.dataset.query = item.query;
    row.dataset.key = item.key;

    const content = document.createElement("div");
    content.className = "flex-grow-1 text-truncate me-2";

    const label = document.createElement("div");
    label.className = "text-truncate fw-medium";
    label.textContent = item.label || item.query;

    const weatherEl = document.createElement("div");
    weatherEl.className = "sidebar-weather text-truncate";
    if (item.weather && item.weather.status === "ok") {
      const desc = item.weather.description || "";
      weatherEl.textContent = `${formatTemp(item.weather.temperature_c)} · ${desc}`;
    } else {
      weatherEl.textContent = "No data yet";
    }

    content.appendChild(label);
    content.appendChild(weatherEl);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn btn-sm btn-outline-secondary flex-shrink-0";
    removeBtn.setAttribute("aria-label", `Remove ${item.label || item.query} from favorites`);
    removeBtn.textContent = "×";
    removeBtn.dataset.key = item.key;

    row.appendChild(content);
    row.appendChild(removeBtn);
    list.appendChild(row);
  }

  updateStarButton();
}

async function loadFavoritesSidebar() {
  try {
    const response = await fetch("/api/favorites/weather");
    if (!response.ok) return;
    const data = await response.json();
    favorites = data.favorites || [];
    renderFavoritesSidebar(favorites);
  } catch {
    /* ignore — list stays empty */
  }
}

async function addFavorite(query, label) {
  const response = await fetch("/api/favorites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, label }),
  });
  if (!response.ok) return false;
  await loadFavoritesSidebar();
  return true;
}

async function removeFavoriteByKey(key) {
  const response = await fetch(`/api/favorites/${encodeURIComponent(key)}`, {
    method: "DELETE",
  });
  if (!response.ok) return false;
  await loadFavoritesSidebar();
  return true;
}

async function handleFavoriteToggle() {
  if (!currentKey || !currentQuery) return;

  const button = document.getElementById("favorite-toggle");
  if (button) button.disabled = true;

  try {
    if (isFavorited(currentKey)) {
      await removeFavoriteByKey(currentKey);
    } else {
      const label = document.getElementById("city-name")?.textContent || currentQuery;
      await addFavorite(currentQuery, label);
    }
  } finally {
    if (button) button.disabled = false;
  }
}

async function loadFavoriteWeather(query) {
  const input = document.getElementById("city");
  if (input) input.value = query;

  const key = cacheKey(query);
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

  setLoading(true);
  try {
    const data = await fetchWeather(query, false);
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

function initFavorites() {
  const toggle = document.getElementById("favorite-toggle");
  if (toggle) {
    toggle.addEventListener("click", handleFavoriteToggle);
  }

  const list = document.getElementById("favorites-sidebar-list");
  if (list) {
    list.addEventListener("click", (event) => {
      const removeBtn = event.target.closest("button[data-key]");
      if (removeBtn) {
        event.preventDefault();
        event.stopPropagation();
        removeFavoriteByKey(removeBtn.dataset.key);
        return;
      }

      const row = event.target.closest("[data-query]");
      if (row?.dataset.query) {
        loadFavoriteWeather(row.dataset.query);
      }
    });
  }

  const button = document.getElementById("favorite-toggle");
  if (button?.dataset.query) {
    currentQuery = button.dataset.query;
    currentKey = cacheKey(currentQuery);
  }

  loadFavoritesSidebar();
}

function renderError(data, hint) {
  if (data.status === "ok" || (data.stale && data.temperature_c != null)) {
    renderWeather(data, hint || data.warning);
    return;
  }

  currentQuery = data.query || data.city || null;
  currentKey = currentQuery ? cacheKey(currentQuery) : null;

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
  updateStarButton();
  loadFavoritesSidebar();
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
  return response.json().catch(() => ({ error: "Server error"}));
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
  initFavorites();
  const form = document.getElementById("search-form");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});
