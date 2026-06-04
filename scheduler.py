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


def _scheduled_refresh() -> None:
    refresh_weather(force=True)


def init_scheduler(app=None) -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    interval = _refresh_interval_minutes()
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _scheduled_refresh,
        "interval",
        minutes=interval,
        id="weather_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Weather scheduler started (every %s minutes)", interval)

    _scheduled_refresh()

    atexit.register(shutdown_scheduler)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Weather scheduler stopped")
