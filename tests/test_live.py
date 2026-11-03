"""
Checks against the real camptocamp.org servers, read only and anonymous.

They detect that a server changed in a way that breaks the bot (this is how
the forum SSO change was found). Skipped unless CAMPBOT_LIVE=1, they run every
week in the `live` workflow.
"""

import os
from urllib.parse import urlparse, parse_qs

import pytest
import requests

pytestmark = pytest.mark.skipif(
    os.environ.get("CAMPBOT_LIVE") != "1", reason="set CAMPBOT_LIVE=1 to run"
)


def test_forum_starts_the_sso_with_a_session_cookie():
    # first step of CampBot.login: the forum session asks for a nonce and the
    # forum must hand back a signed payload for the API, and a session cookie
    # to which that nonce is bound
    response = requests.get(
        "https://forum.camptocamp.org/session/sso", allow_redirects=False, timeout=30
    )

    assert response.status_code == 302
    location = urlparse(response.headers["Location"])
    query = parse_qs(location.query)
    assert location.netloc.endswith("camptocamp.org")
    assert query["sso"] and query["sig"]
    assert response.cookies, "the nonce must be bound to a session cookie"


def test_api_gives_a_route():
    from campbot import CampBot

    route = CampBot(min_delay=0).wiki.get_route(56915)

    assert route.document_id == 56915
    assert route["locales"]


def test_api_lists_recent_changes():
    from campbot import CampBot

    bot = CampBot(min_delay=0)
    changes = bot.wiki.get("/documents/changes", limit=5)

    assert changes["feed"]


def test_forum_answers():
    from campbot import CampBot

    about = CampBot(min_delay=0).forum.get("/about.json")

    assert about["about"]["stats"]
