# coding: utf-8

from __future__ import print_function, unicode_literals, division

import pytest
import json
import io
import os

MESSAGE_URL = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480/1"


def get_message(filename):
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/" + filename + ".json")
    return json.load(io.open(filename))


messages = {
    ("GET", "https://forum.camptocamp.org/session/csrf"): {"csrf": "csrf"},
    ("GET", "https://api.camptocamp.org/documents/changes?limit=50&u=271988"): {"feed": []},
    ("POST", "https://api.camptocamp.org/users/login"): {"token": "", "redirect_internal": "/sso", "roles": []},
    ('GET', 'https://forum.camptocamp.org/sso'): {},
    ('POST', 'https://forum.camptocamp.org/posts'): {},
    ('PUT', 'https://api.camptocamp.org/profiles/286726'): {},
    ('PUT', 'https://api.camptocamp.org/routes/293549'): {},

    ('GET', 'https://api.camptocamp.org/outings?offset=0&u=286726'): get_message("outings"),
    ('GET', 'https://api.camptocamp.org/outings?u=286726&offset=0'): get_message("outings"),
    ('GET', 'https://api.camptocamp.org/outings?offset=30&u=286726'): {"documents": []},
    ('GET', 'https://api.camptocamp.org/outings?u=286726&offset=30'): {"documents": []},
    ('GET', 'https://api.camptocamp.org/routes?offset=0'): get_message("routes"),

    ("GET", "https://api.camptocamp.org/documents/changes?limit=50"): get_message("changes"),

    ('GET', 'https://forum.camptocamp.org/t/201480.json'): get_message("topic"),
    ('GET', 'https://forum.camptocamp.org/posts/2003993.json'): get_message("post"),

    ('GET', 'https://api.camptocamp.org/routes/293549/fr/1738922'): get_message("route_version"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/1738528'): get_message("route_version"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/880880'): get_message("route_version2"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/978249'): get_message("route_version2"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/478470'): get_message("route_version2"),
    ('GET', 'https://api.camptocamp.org/routes/293549'): get_message("route"),

    ('GET', 'https://api.camptocamp.org/waypoints/952999'): get_message("waypoint"),
    ('GET', 'https://api.camptocamp.org/search?q=CharlesB&t=u&limit=50'): get_message("search_user"),
    ('GET', 'https://api.camptocamp.org/search?q=grimpeur8b&t=u&limit=50'): get_message("search_user"),
    ('GET', 'https://api.camptocamp.org/search?q=unknown&t=u&limit=50'): get_message("search_user"),
    ('GET', 'https://api.camptocamp.org/profiles/286726'): get_message("user"),
    ('GET', 'https://api.camptocamp.org/profiles/3199'): get_message("user"),
    ('GET', 'https://api.camptocamp.org/profiles/271988'): get_message("user"),
    ('GET', 'https://api.camptocamp.org/profiles/567073'): get_message("user"),
    ('GET', 'https://api.camptocamp.org/documents/changes?limit=50&u=286726'): get_message("changes"),
    ('GET', 'https://api.camptocamp.org/documents/changes?limit=50&u=567073'): get_message("changes"),
    ('GET', 'https://forum.camptocamp.org/groups/Association/members.json?limit=50&offset=0'): get_message("groups"),
    ('GET',
     'https://forum.camptocamp.org/polls/voters.json?post_id=2003993&poll_name=poll&option_id=option_id&offset=0'):
        {"poll": {"option_id": [{"username": "CharlesB"}, {"username": "grimpeur8b"}]}},
    ('GET',
     'https://forum.camptocamp.org/polls/voters.json?post_id=2003993&poll_name=poll&option_id=option_id&offset=1'):
        {"poll": {}},
}


@pytest.yield_fixture()
def ids_files():
    with io.open("ids_test.txt", "w") as f:
        f.write("293549|r")

    yield "ids_test.txt"


@pytest.fixture()
def fix_requests():
    from requests import Session
    from campbot.core import BaseBot

    class Response():
        def __init__(self, method, url, **kwargs):
            self.status = 200
            self.headers = {'Content-type': 'application/json'}
            self._data = messages[(method, url)]

            print(method, url, kwargs)

        def raise_for_status(self):
            if self.status != 200:
                raise Exception("")

        def json(self):
            return self._data

    def request(self, method, url, **kwargs):
        return Response(method, url, **kwargs)

    BaseBot.min_delay = 0.001

    Session.request = request


def test_check_voters(fix_requests):
    from campbot.__main__ import main

    main(get_main_args("check_voters"))


def test_exports(fix_requests):
    from campbot.__main__ import main

    main(get_main_args("contributions"))
    main(get_main_args("outings"))


def test_forum(fix_requests):
    from campbot import CampBot

    CampBot().forum.get_group_members(group_name="Association")
    CampBot().forum.get_participants(MESSAGE_URL)


def test_wiki(fix_requests):
    from campbot import CampBot, objects

    for _ in CampBot().wiki.get_route_ids():
        break

    for _ in CampBot().wiki.get_documents(objects.Route):
        break

    CampBot().wiki.get_wiki_object_version(None, "", "", None)
    CampBot().wiki.get_wiki_object(item_id=293549, document_type="r")
    CampBot().wiki.get_route(route_id=293549)
    CampBot().wiki.get_contributions(oldest_date="2017-12-12", newest_date="2017-12-13")

    waypoint = CampBot().wiki.get_waypoint(waypoint_id=952999)

    waypoint.get_invalidity_reason()

    assert CampBot().wiki.get_user(forum_name="unknown") is None

    user = CampBot().wiki.get_user(forum_name="CharlesB")
    contrib = user.get_last_contribution()
    contrib.get_full_document()
    contrib.user.get_wiki_user()
    user.save("test")


def test_login(fix_requests):
    from campbot import CampBot

    CampBot().login("x", "y")


def test_recent_changes(fix_requests):
    from campbot.__main__ import main

    main(get_main_args("check_recent_changes"))


def test_fix_bbcode(fix_requests, ids_files):
    from campbot.__main__ import main

    from campbot import CampBot, LtagCleaner

    main(get_main_args("remove_bbcode", {"<ids_file>": ids_files}))
    main(get_main_args("remove_bbcode2", {"<ids_file>": ids_files}))
    main(get_main_args("clean_color_u", {"<ids_file>": ids_files}))

    CampBot().fix_markdown(LtagCleaner(), ids_files, False)


def get_main_args(action, others=None):
    # noinspection PyDictCreation
    result = {
        "remove_bbcode": False,
        "remove_bbcode2": False,
        "clean_color_u": False,
        "check_recent_changes": False,
        "check_voters": False,
        "contributions": False,
        "outings": False,
        "--delay": 0.01,
        "--login": "x",
        "--password": "y",
        "--lang": "fr",
        "--batch": True,
        "<message_url>": MESSAGE_URL,
        "<filters>": "u=286726",
        "--ends": "2999-12-31",
        "--starts": "2017-06-01",
        "--out": "",
    }

    if others:
        result.update(others)

    result[action] = True

    return result
