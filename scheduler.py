from __future__ import annotations

import atexit
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from fetcher import refresh_weather

load_dotenv()

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _refresh_interval_minutes() -> int:
    return int(os.getenv("REFRESH_INTERVAL_MINUTES", "15"))


def init_scheduler(app=None) -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    interval = _refresh_interval_minutes()
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        refresh_weather,
        "interval",
        minutes=interval,
        id="weather_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Weather scheduler started (every %s minutes)", interval)

    refresh_weather()

    atexit.register(shutdown_scheduler)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Weather scheduler stopped")
