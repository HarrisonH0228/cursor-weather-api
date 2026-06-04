import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

from fetcher import get_cached_weather, refresh_weather
from scheduler import init_scheduler

load_dotenv()


def create_app(enable_scheduler: bool = True) -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"
    app.config["CACHE_TTL_MINUTES"] = int(os.getenv("CACHE_TTL_MINUTES", "15"))

    @app.route("/")
    def index():
        weather = get_cached_weather()
        if weather.get("status") != "ok":
            return (
                render_template(
                    "_error.html",
                    weather=weather,
                    cache_ttl_minutes=app.config["CACHE_TTL_MINUTES"],
                    default_city=os.getenv("DEFAULT_CITY", "San Francisco"),
                ),
                503,
            )
        return render_template(
            "index.html",
            weather=weather,
            cache_ttl_minutes=app.config["CACHE_TTL_MINUTES"],
            default_city=os.getenv("DEFAULT_CITY", "San Francisco"),
        )

    @app.route("/refresh", methods=["POST"])
    def refresh():
        city = request.form.get("city", "").strip() or None
        force = request.form.get("force") == "true"
        refresh_weather(city, force=force)
        return redirect(url_for("index"))

    @app.route("/api/refresh", methods=["POST"])
    def api_refresh():
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or request.form.get("city") or "").strip() or None
        force = bool(data.get("force")) or request.form.get("force") == "true"
        result = refresh_weather(city, force=force)
        return jsonify(result), 200

    @app.route("/api/weather")
    def api_weather():
        city = request.args.get("city", "").strip() or None
        weather = get_cached_weather(city)
        if not weather:
            return jsonify({"error": "No cached weather for that city"}), 404
        return jsonify(weather), 200

    if enable_scheduler:
        init_scheduler(app)
    return app
