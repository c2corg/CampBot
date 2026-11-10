"""Requests refused because of rate limiting (429) are retried after the wait asked."""

import json
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest
import requests

from campbot import CampBot


def _response(status, payload=None, headers=None):
    res = requests.Response()
    res.status_code = status
    res.headers["Content-type"] = "application/json"
    res.headers.update(headers or {})
    res._content = json.dumps(payload or {}).encode()
    return res


def fake_server(monkeypatch, answers):
    """Answer each request with the next of answers: a status, or (status, payload[, headers])"""
    calls = []
    answers = list(answers)

    def request(self, method, url, **kwargs):
        calls.append(dict(kwargs, method=method, url=url))
        answer = answers.pop(0)
        if isinstance(answer, int):
            answer = (answer,)
        return _response(*answer)

    monkeypatch.setattr(requests.Session, "request", request)
    return calls


@pytest.fixture()
def sleeps(monkeypatch):
    sleeps = []
    monkeypatch.setattr("campbot.core.time.sleep", sleeps.append)
    return sleeps


@pytest.fixture()
def bot():
    return CampBot(min_delay=0)


def test_rate_limited_get_is_retried_after_retry_after(monkeypatch, sleeps, bot):
    calls = fake_server(
        monkeypatch, [(429, None, {"Retry-After": "5"}), (200, {"ok": True})]
    )

    assert bot.wiki.get("/routes", offset=30) == {"ok": True}
    assert len(calls) == 2
    assert calls[1]["params"] == {"offset": 30}
    assert 7 in sleeps  # 5s + margin


def test_discourse_wait_seconds_wins_over_retry_after(monkeypatch, sleeps, bot):
    fake_server(
        monkeypatch,
        [(429, {"extras": {"wait_seconds": 12}}, {"Retry-After": "5"}), 200],
    )

    bot.forum.get("/t/1.json")

    assert 14 in sleeps and 7 not in sleeps


def test_retry_after_as_a_date(monkeypatch, sleeps, bot):
    date = datetime.now(timezone.utc) + timedelta(seconds=60)
    fake_server(
        monkeypatch,
        [(429, None, {"Retry-After": format_datetime(date, usegmt=True)}), 200],
    )

    bot.wiki.get("/routes")

    assert any(55 < s <= 62 for s in sleeps)


def test_rate_limited_without_hint_waits_30s(monkeypatch, sleeps, bot):
    fake_server(monkeypatch, [429, 200])

    bot.wiki.get("/routes")

    assert 32 in sleeps


def test_post_and_put_are_retried_with_the_same_body(monkeypatch, sleeps, bot):
    calls = fake_server(monkeypatch, [429, 200, 429, 200])

    bot.forum.post("/posts", {"raw": "coucou"})
    bot.forum.put("/groups/1/members.json", {"usernames": "x"})

    assert [(c["method"], c["json"]) for c in calls] == [
        ("POST", {"raw": "coucou"}),
        ("POST", {"raw": "coucou"}),
        ("PUT", {"usernames": "x"}),
        ("PUT", {"usernames": "x"}),
    ]


def test_unavailable_is_retried_only_when_told_when(monkeypatch, sleeps, bot):
    calls = fake_server(monkeypatch, [(503, None, {"Retry-After": "10"}), 200, 503])

    bot.wiki.get("/routes")
    assert len(calls) == 2 and 12 in sleeps

    with pytest.raises(requests.HTTPError):
        bot.wiki.get("/routes")
    assert len(calls) == 3


def test_gives_up_after_max_retries(monkeypatch, sleeps, bot):
    calls = fake_server(monkeypatch, [429] * 10)

    with pytest.raises(requests.HTTPError) as error:
        bot.wiki.get("/routes")

    assert error.value.response.status_code == 429
    assert len(calls) == bot.wiki.max_retries + 1


def test_does_not_wait_longer_than_max_wait(monkeypatch, sleeps, bot):
    calls = fake_server(monkeypatch, [(429, None, {"Retry-After": "3600"}), 200])

    with pytest.raises(requests.HTTPError):
        bot.wiki.get("/routes")

    assert len(calls) == 1
    assert not any(s >= 300 for s in sleeps)


@pytest.mark.parametrize("status", [400, 403, 404, 500, 502])
def test_other_errors_are_not_retried(monkeypatch, sleeps, bot, status):
    calls = fake_server(monkeypatch, [status, 200])

    with pytest.raises(requests.HTTPError):
        bot.wiki.get("/routes")

    assert len(calls) == 1


def test_requests_are_slower_once_rate_limited(monkeypatch, sleeps):
    bot = CampBot(min_delay=0.01)
    fake_server(monkeypatch, [429, 200, 429, 200])

    bot.wiki.get("/routes")
    assert bot.wiki.min_delay == timedelta(seconds=0.1)

    bot.wiki.get("/routes")
    assert bot.wiki.min_delay == timedelta(seconds=0.2)

    assert bot.forum.min_delay == timedelta(seconds=0.01)  # forum not limited


def test_a_long_delay_set_by_the_user_is_kept(monkeypatch, sleeps):
    bot = CampBot(min_delay=60)
    fake_server(monkeypatch, [429, 200])

    bot.wiki.get("/routes")

    assert bot.wiki.min_delay == timedelta(seconds=60)
