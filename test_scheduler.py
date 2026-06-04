import scheduler


def test_scheduled_refresh_calls_force_true(monkeypatch):
    calls = []

    def recorder(city=None, force=False):
        calls.append({"city": city, "force": force})
        return {"status": "ok", "from_cache": False}

    monkeypatch.setattr(scheduler, "refresh_weather", recorder)
    scheduler._scheduled_refresh()

    assert len(calls) == 1
    assert calls[0]["city"] is None
    assert calls[0]["force"] is True
