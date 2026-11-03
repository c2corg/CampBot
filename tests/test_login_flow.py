"""
Functional test of the camptocamp.org / forum sign-in.

The sign-in involves two servers (the API and the Discourse forum). A recent
Discourse binds the SSO nonce to the session cookie of the browser that asked
for it, and answers 419 otherwise. This fake of both servers enforces that
rule, so the test fails if the bot lets another session ask for the nonce.
"""

import io
import json
from urllib.parse import urlparse, parse_qs

import pytest
import requests
from requests.adapters import BaseAdapter
from requests.structures import CaseInsensitiveDict


class FakeC2C(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.nonces = {}  # nonce -> id of the forum session that asked for it
        self.counter = 0
        self.calls = []
        self.sessions = {}  # host -> requests.Session, to set cookies

    # helpers

    def _new_id(self, prefix):
        self.counter += 1
        return "%s%d" % (prefix, self.counter)

    def _response(self, request, status, body=b"", content_type="text/html", **headers):
        response = requests.Response()
        response.status_code = status
        response.url = request.url
        response.request = request
        response._content = body
        response.raw = io.BytesIO(b"")
        response.headers = CaseInsensitiveDict(headers)
        response.headers["Content-type"] = content_type
        return response

    def _json(self, request, data, status=200):
        return self._response(
            request, status, json.dumps(data).encode(), "application/json"
        )

    def _cookie(self, request, name):
        cookies = request.headers.get("Cookie", "")
        for item in cookies.split(";"):
            key, _, value = item.strip().partition("=")
            if key == name:
                return value
        return None

    # the servers

    def send(self, request, **kwargs):
        url = urlparse(request.url)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        self.calls.append((request.method, url.netloc, url.path))

        if url.netloc == "forum.camptocamp.org":
            return self._forum(request, url, query)
        if url.netloc == "api.camptocamp.org":
            return self._api(request, url, query)
        raise AssertionError("unexpected request to %s" % request.url)

    def _forum(self, request, url, query):
        session = self.sessions["forum.camptocamp.org"]

        if url.path == "/session/sso":
            sid = self._cookie(request, "_forum_session")
            if not sid:
                sid = self._new_id("forum-session-")
                session.cookies.set("_forum_session", sid, domain=url.netloc)
            nonce = self._new_id("nonce-")
            self.nonces[nonce] = sid
            location = "https://www.camptocamp.org/auth-sso?sso=%s&sig=sig-%s" % (
                nonce,
                nonce,
            )
            return self._response(request, 302, Location=location)

        if url.path == "/session/sso_login":
            nonce = query.get("sso")
            sid = self._cookie(request, "_forum_session")
            valid = (
                nonce in self.nonces
                and self.nonces.pop(nonce) == sid
                and query.get("sig") == "sig-%s" % nonce
            )
            if not valid:
                return self._response(request, 419, b"nonce is incorrect")
            session.cookies.set("_t", "logged-in", domain=url.netloc)
            return self._response(
                request, 302, Location="https://forum.camptocamp.org/"
            )

        if url.path == "/session/csrf":
            return self._json(request, {"csrf": "csrf-token"})

        return self._response(request, 200, b"<html></html>")

    def _api(self, request, url, query):
        if url.path == "/users/login":
            body = json.loads(request.body)
            assert body["username"] == "bot" and body["password"] == "secret"
            answer = {"token": "jwt", "roles": ["moderator"], "username": "bot"}

            if "sso" in body and "sig" in body:
                answer["redirect"] = (
                    "https://forum.camptocamp.org/session/sso_login?sso=%s&sig=%s"
                    % (body["sso"], body["sig"])
                )
            else:
                # what the API does without a nonce from the caller: it asks
                # Discourse itself, from its own session
                nonce = self._new_id("nonce-")
                self.nonces[nonce] = "api-session"
                answer["redirect_internal"] = (
                    "https://forum.camptocamp.org/session/sso_login?sso=%s&sig=sig-%s"
                    % (nonce, nonce)
                )
            return self._json(request, answer)

        raise AssertionError("unexpected API call %s" % request.url)

    def close(self):
        pass


@pytest.fixture()
def fake_c2c():
    return FakeC2C()


def make_bot(fake):
    from campbot import CampBot

    bot = CampBot(min_delay=0)
    for host, base in (
        ("forum.camptocamp.org", bot.forum),
        ("api.camptocamp.org", bot.wiki),
    ):
        base._session.mount("https://", fake)
        fake.sessions[host] = base._session
    return bot


def test_login_opens_a_forum_session(fake_c2c):
    bot = make_bot(fake_c2c)

    bot.login("bot", "secret")

    assert bot.moderator
    assert bot.wiki.headers["Authorization"] == 'JWT token="jwt"'
    assert bot.forum.headers["X-CSRF-Token"] == "csrf-token"
    assert bot.forum._session.cookies.get("_t") == "logged-in"


def test_login_asks_the_nonce_to_the_forum_session(fake_c2c):
    bot = make_bot(fake_c2c)

    bot.login("bot", "secret")

    forum_calls = [path for _, host, path in fake_c2c.calls if "forum" in host]
    assert forum_calls[:2] == ["/session/sso", "/session/sso_login"]


def test_the_fake_forum_refuses_a_nonce_asked_by_another_session(fake_c2c):
    # sanity check of this test: it must fail when the API asks the nonce
    bot = make_bot(fake_c2c)
    answer = bot.wiki.post(
        "/users/login", {"username": "bot", "password": "secret", "discourse": True}
    )

    url = answer["redirect_internal"].replace(bot.forum.api_url, "")
    with pytest.raises(requests.HTTPError) as error:
        bot.forum.get(url)

    assert error.value.response.status_code == 419
