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
    ("GET", "https://api.camptocamp.org/documents/changes?limit=50&token=1687339"): {"feed": []},

    ("POST", "https://api.camptocamp.org/users/login"): {"token": "", "redirect_internal": "/sso", "roles": []},

    ('PUT', 'https://api.camptocamp.org/profiles/286726'): {},
    ('PUT', 'https://api.camptocamp.org/routes/293549'): {},

    ('GET', 'https://api.camptocamp.org/outings?offset=0&u=286726'): get_message("outings"),
    ('GET', 'https://api.camptocamp.org/outings?u=286726&offset=0'): get_message("outings"),

    ('GET', 'https://api.camptocamp.org/outings?offset=30&u=286726'): {"documents": []},
    ('GET', 'https://api.camptocamp.org/outings?u=286726&offset=30'): {"documents": []},

    ('GET', 'https://api.camptocamp.org/routes?offset=0'): get_message("routes"),
    ('GET', 'https://api.camptocamp.org/xreports?offset=0'): get_message("routes"),

    ("GET", "https://api.camptocamp.org/documents/changes?limit=50"): get_message("changes"),

    ('GET', 'https://forum.camptocamp.org/sso'): {},
    ('POST', 'https://forum.camptocamp.org/posts'): {},
    ('GET', 'https://forum.camptocamp.org/t/201480.json?username_filters=rabot'): {"last_posted_at": "2020/01/01"},
    ('GET', 'https://forum.camptocamp.org/t/201480.json'): get_message("topic"),
    ('GET', 'https://forum.camptocamp.org/posts/2003993.json'): get_message("post"),

    ('GET', 'https://api.camptocamp.org/routes/293549/fr/1738922'): get_message("route_version"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/1738528'): get_message("route_version"),

    ('GET', 'https://api.camptocamp.org/routes/293549/fr/880880'): get_message("route_version2"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/978249'): get_message("route_version2"),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/478470'): get_message("route_version2"),

    ('GET', 'https://api.camptocamp.org/routes/293549'): get_message("route"),
    ('GET', 'https://api.camptocamp.org/routes/123'): get_message("route"),
    ('GET', 'https://api.camptocamp.org/routes/123'): get_message("route"),
    ('GET', 'https://api.camptocamp.org/routes/953061'): get_message("route"),

    ('GET', 'https://api.camptocamp.org/routes/123/fr/123'): get_message("redirection"),
    ('GET', 'https://api.camptocamp.org/routes/123/fr/122'): get_message("redirection"),

    ('GET', 'https://api.camptocamp.org/articles/996571'): get_message("conf_replacements"),

    ('GET', 'https://api.camptocamp.org/waypoints/952999'): get_message("waypoint"),
    ('GET', 'https://api.camptocamp.org/search?q=CharlesB&t=u&limit=50'): get_message("search_user"),
    ('GET', 'https://api.camptocamp.org/search?q=grimpeur8b&t=u&limit=50'): get_message("search_user"),
    ('GET', 'https://api.camptocamp.org/search?q=unknown&t=u&limit=50'): get_message("search_user"),

    ('GET', 'https://api.camptocamp.org/outings/946946'): get_message("outing"),
    ('GET', 'https://api.camptocamp.org/outings/946945'): get_message("outing"),

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


@pytest.yield_fixture()
def fix_dump():
    from campbot import dump

    _default_db_name = dump._default_db_name
    dump._default_db_name = "test.db"

    yield

    dump._default_db_name = _default_db_name


@pytest.fixture()
def fix_requests():
    from requests import Session
    from campbot import core
    import datetime

    core.today = lambda: datetime.datetime(year=2017, month=12, day=21)

    class Response(object):
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

    core.BaseBot.min_delay = 0.001

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

    for _ in CampBot().wiki.get_document_ids(document_type="r"):
        break

    for _ in CampBot().wiki.get_route_ids():
        break

    for _ in CampBot().wiki.get_xreport_ids():
        break

    for _ in CampBot().wiki.get_documents(constructor=objects.Route):
        break

    assert CampBot().wiki.ui_url == "https://www.camptocamp.org"

    version = CampBot().wiki.get_wiki_object_version(293549, "r", "fr", 1738922)
    assert version.get_diff_url("fr") is not None
    assert version.get_locale_length("fr") != 0

    CampBot().wiki.get_wiki_object_version(None, "", "", None)

    route = CampBot().wiki.get_wiki_object(item_id=293549, document_type="r")
    assert route.get_url() == "https://www.camptocamp.org/routes/293549"
    assert route.get_history_url("fr") == "https://www.camptocamp.org/routes/history/293549/fr"

    CampBot().wiki.get_route(route_id=293549)
    CampBot().wiki.get_contributions(oldest_date="2017-12-12", newest_date="2017-12-13")

    waypoint = CampBot().wiki.get_waypoint(waypoint_id=952999)

    waypoint.get_invalidity_reason()

    with pytest.raises(Exception):
        CampBot().wiki.get_user(forum_name="unknown")

    user = CampBot().wiki.get_user(forum_name="CharlesB")
    user.is_personal()
    contrib = user.get_last_contribution()
    contrib.get_full_document()
    contrib.user.get_wiki_user()
    user.save("test", ask_before_saving=False)


def test_login(fix_requests):
    from campbot import CampBot

    CampBot().login("x", "y")


def test_recent_changes(fix_requests):
    from campbot.__main__ import main

    main(get_main_args("check_recent_changes"))


def test_dump(fix_requests, fix_dump):
    from campbot.dump import Dump, get_document_types, _search
    from campbot import CampBot

    get_document_types()

    route = CampBot().wiki.get_route(123)

    class Contrib():
        document = route

    dump = Dump()
    dump.insert(dump._conn.cursor(), route, 1687340, Contrib)
    dump._conn.commit()
    dump.complete()
    dump.select(123)
    dump.search("r")
    dump.get_all_ids()

    _search("r")

    os.remove("test.db")


def test_fix_bbcode(fix_requests, ids_files):
    from campbot.__main__ import main

    from campbot import CampBot
    from campbot.processors import LtagCleaner

    main(get_main_args("remove_bbcode", {"<ids_file>": ids_files}))
    main(get_main_args("remove_bbcode2", {"<ids_file>": ids_files}))
    main(get_main_args("clean_color_u", {"<ids_file>": ids_files}))

    CampBot().fix_markdown(LtagCleaner(), ids_files, False)


def get_main_args(action, others=None):
    # noinspection PyDictCreation
    result = {
        "check_rc": False,
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


def test_processors():
    from campbot.processors import InternalLinkCorrector, MarkdownCleaner, LtagMigrator

    InternalLinkCorrector().modify("[[123|coucou]]")
    MarkdownCleaner().modify("[[123|coucou]]")
    LtagMigrator().modify("L# ")


def test_checkers(fix_requests):
    from campbot.checkers import LengthTest, ReTest, HistoryTest, MainWaypointTest, RouteTypeTest
    from campbot import CampBot
    from campbot.objects import Contribution

    bot = CampBot()

    route = bot.wiki.get_route(123)
    contrib = Contribution(bot, {"document": route, "user": {}})

    LengthTest("fr")(None, contrib, contrib)
    HistoryTest("fr")(None, contrib, contrib)
    MainWaypointTest()(None, contrib, contrib)
    RouteTypeTest()(None, contrib, contrib)

    t = ReTest("x", "fr")
    t.patterns.append("e")
    t(None, contrib, contrib)
