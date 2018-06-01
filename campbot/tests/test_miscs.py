# coding: utf-8

from __future__ import print_function, unicode_literals, division

from campbot.tests.fixtures import fix_requests, fix_dump
import os
import pytest

MESSAGE_URL = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480/1"


def test_post_message(fix_requests):
    from campbot import CampBot

    url = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480"

    bot = CampBot()

    bot.forum.post_message("coucou", url)


def test_check_voters(fix_requests):
    from campbot import CampBot

    CampBot().check_voters(url=MESSAGE_URL, allowed_groups=("Association",))


def test_main_entry_point(fix_requests):
    from campbot.__main__ import main

    main(get_main_args("contribs"))
    main(get_main_args("export"))
    main(get_main_args("check_rc"))
    main(get_main_args("clean", {"<url>": "routes#w=123"}))


def test_forum(fix_requests):
    from campbot import CampBot

    CampBot().forum.get_group_members(group_name="Association")
    CampBot().forum.get_participants(MESSAGE_URL)
    CampBot().forum.get_post(url=MESSAGE_URL)
    CampBot().forum.get_last_message_timestamp(url=MESSAGE_URL, username="rabot")


def test_wiki(fix_requests):
    from campbot import CampBot, objects

    route = CampBot().wiki.get_route(route_id=293549)
    route.is_personal()

    xreport = CampBot().wiki.get_xreport(xreport_id=293549)
    xreport.is_personal()

    image = CampBot().wiki.get_image(image_id=1005116)
    image.is_personal()

    CampBot().wiki.get_profile(profile_id=293549)
    CampBot().wiki.get_area(area_id=293549)
    CampBot().wiki.get_book(book_id=293549)
    CampBot().wiki.get_map(map_id=293549)

    list(CampBot().wiki.get_routes({}))
    list(CampBot().wiki.get_waypoints({}))
    list(CampBot().wiki.get_outings({}))

    for _ in CampBot().wiki.get_route_ids():
        break

    for _ in CampBot().wiki.get_xreport_ids():
        break

    for _ in CampBot().wiki.get_document_ids(document_type="r"):
        break

    for _ in CampBot().wiki.get_documents(document_type="r"):
        break

    assert CampBot().wiki.ui_url == "https://www.camptocamp.org"

    version = CampBot().wiki.get_wiki_object_version(293549, "r", "fr", 1738922)
    assert version.get_diff_url("fr") is not None
    assert version.get_locale_length("fr") != 0

    CampBot().wiki.get_wiki_object_version(None, "", "", None)

    route = CampBot().wiki.get_wiki_object(item_id=293549, document_type="r")
    assert route.get_url() == "https://www.camptocamp.org/routes/293549"
    assert route.get_history_url("fr") == "https://www.camptocamp.org/routes/history/293549/fr"

    CampBot().wiki.get_contributions(oldest_date="2017-12-12", newest_date="2017-12-13")

    waypoint = CampBot().wiki.get_waypoint(waypoint_id=952999)

    waypoint.get_invalidity_reason()

    with pytest.raises(Exception):
        CampBot().wiki.get_user(forum_name="unknown")

    user = CampBot().wiki.get_user(forum_name="CharlesB")
    user.is_personal()
    user.save("test", ask_before_saving=False)

    contrib = user.get_last_contribution()
    contrib.get_full_document()
    contrib.user.get_wiki_user()
    contrib.user.is_newbie()
    contrib.user.get_contributions_url()


def test_login(fix_requests):
    from campbot import CampBot

    CampBot().login("x", "y")


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

    del dump
    os.remove("test.db")


def test_misc():
    from campbot import core

    core.today()


def get_main_args(action, others=None):
    # noinspection PyDictCreation
    result = {
        "check_rc": False,
        "check_voters": False,
        "contribs": False,
        "export": False,
        "clean": False,
        "--delay": 0.01,
        "--login": "x",
        "--password": "y",
        "--lang": "fr",
        "--batch": True,
        "<url>": "outings#u=286726",
        "--ends": "2999-12-31",
        "--starts": "2017-06-01",
        "--out": "",
    }

    if others:
        result.update(others)

    assert action in result

    result[action] = True

    os.environ["HTTPS_PROXY"] = ""
    os.environ["CAMPBOT_CREDENTIALS"] = "patate@douce"

    return result


def test_checkers(fix_requests):
    from campbot.checkers import LengthTest, ReTest, HistoryTest, MainWaypointTest, RouteTypeTest
    from campbot import CampBot
    from campbot.objects import Contribution

    bot = CampBot()

    route = bot.wiki.get_route(123)
    contrib = Contribution(bot, {"document": route, "user": {}})

    LengthTest("fr")(None, contrib, contrib)

    LengthTest("fr")(None, None, contrib)
    LengthTest("fr")(None, contrib, None)

    HistoryTest("fr")(None, contrib, contrib)
    MainWaypointTest()(None, contrib, contrib)
    RouteTypeTest()(None, contrib, contrib)

    t = ReTest("x", "fr")
    t.patterns.append("e")
    t(None, contrib, contrib)
