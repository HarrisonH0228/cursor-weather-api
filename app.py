import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from favorites import add_favorite, list_favorites, remove_favorite
from fetcher import get_cached_weather, get_display_weather, refresh_weather
from scheduler import init_scheduler

load_dotenv()

logger = logging.getLogger(__name__)


def _template_context(app: Flask) -> dict:
    return {
        "cache_ttl_minutes": app.config["CACHE_TTL_MINUTES"],
        "default_city": os.getenv("DEFAULT_CITY", "San Francisco"),
    }


def create_app(enable_scheduler: bool = True) -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"
    app.config["CACHE_TTL_MINUTES"] = int(os.getenv("CACHE_TTL_MINUTES", "15"))
    app.config["PROPAGATE_EXCEPTIONS"] = False

    def _search_handler():
        data = request.get_json(silent=True) or {}
        city = (data.get("city") or request.form.get("city") or "").strip() or None
        force = bool(data.get("force")) or request.form.get("force") == "true"
        return refresh_weather(city, force=force)

    @app.route("/")
    def index():
        weather = get_display_weather()
        ctx = _template_context(app)
        if weather.get("status") != "ok":
            return (
                render_template(
                    "_error.html",
                    weather={
                        "error": "No weather data available yet. Try searching for a city.",
                    },
                    **ctx,
                ),
                503,
            )
        return render_template("index.html", weather=weather, **ctx)

    @app.route("/refresh", methods=["POST"])
    def refresh():
        _search_handler()
        return redirect(url_for("index"))

    @app.route("/search", methods=["POST"])
    @app.route("/api/refresh", methods=["POST"])
    def search():
        result = _search_handler()
        return jsonify(result), 200

    @app.route("/api/weather")
    def api_weather():
        city = request.args.get("city", "").strip() or None
        weather = get_cached_weather(city)
        if not weather:
            return jsonify({"error": "No cached weather for that city"}), 404
        return jsonify(weather), 200

    @app.route("/api/favorites", methods=["GET"])
    def api_favorites_list():
        return jsonify({"favorites": list_favorites()}), 200

    @app.route("/api/favorites", methods=["POST"])
    def api_favorites_add():
        data = request.get_json(silent=True) or {}
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"error": "query is required"}), 400
        label = (data.get("label") or "").strip() or None
        favorites = add_favorite(query, label=label)
        return jsonify({"favorites": favorites}), 200

    @app.route("/api/favorites/<key>", methods=["DELETE"])
    def api_favorites_remove(key):
        favorites = remove_favorite(key)
        if favorites is None:
            return jsonify({"error": "Favorite not found"}), 404
        return jsonify({"favorites": favorites}), 200

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        if e.code == 404:
            return (
                render_template(
                    "_error.html",
                    weather={"error": "Page not found."},
                    **_template_context(app),
                ),
                404,
            )
        return e

    @app.errorhandler(500)
    def handle_500(e):
        logger.exception("Internal server error: %s", e)
        return (
            render_template(
                "_error.html",
                weather={"error": "An unexpected error occurred."},
                **_template_context(app),
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception("Unhandled exception: %s", e)
        return (
            render_template(
                "_error.html",
                weather={"error": "An unexpected error occurred."},
                **_template_context(app),
            ),
            500,
        )

    if os.getenv("FLASK_SKIP_SCHEDULER") == "1":

        @app.route("/__test_raise")
        def __test_raise():
            raise RuntimeError("test failure")

    if enable_scheduler:
        init_scheduler(app)
    return app


app = create_app(enable_scheduler=os.getenv("FLASK_SKIP_SCHEDULER") != "1")
