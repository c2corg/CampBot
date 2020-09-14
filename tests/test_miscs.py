# coding: utf-8

from __future__ import print_function, unicode_literals, division

from tests.fixtures import fix_requests, fix_dump, ids_files, fix_input
import os
import pytest

MESSAGE_URL = (
    "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480/1"
)


def test_distance(fix_requests):
    from campbot import CampBot, utils

    bot = CampBot()

    item1 = bot.wiki.get_route(123)
    item2 = bot.wiki.get_wiki_object_version(293549, "r", "fr", 880880)
    item3 = bot.wiki.get_waypoint(123)

    assert utils.compute_distance(item1, item2) is None
    assert 571.9 < utils.compute_distance(item1, item3) < 572


def test_get_users_from_route(fix_requests):
    from campbot import CampBot

    bot = CampBot()
    bot.get_users_from_route(123)


def test_add_user_to_group(fix_requests):
    from campbot import CampBot

    bot = CampBot()
    bot.forum.add_users_to_group("Association", ["rabot",])


def test_post_message(fix_requests):
    from campbot import CampBot

    url = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480"

    bot = CampBot()

    bot.forum.post_message("coucou", url)


def test_main_entry_point(fix_requests, ids_files):
    from campbot.__main__ import main

    main(get_main_args("contribs"))
    main(get_main_args("export"))
    main(get_main_args("report_rc"))
    main(get_main_args("report", {"<url_or_file>": "routes#w=123"}))
    main(get_main_args("clean_rc"))
    main(get_main_args("clean", {"<url_or_file>": "routes#w=123"}))
    main(get_main_args("clean", {"<url_or_file>": "waypoints#w=123"}))
    main(get_main_args("clean", {"<url_or_file>": ids_files}))

    os.remove("outings.csv")
    os.remove("contributions.csv")


def test_forum(fix_requests):
    from campbot import CampBot

    CampBot().forum.get_group_members(group_name="Association")
    CampBot().forum.get_participants(MESSAGE_URL)
    CampBot().forum.get_post(url=MESSAGE_URL)


def test_saving(fix_requests, fix_input):
    from campbot import CampBot

    fix_input.set_response(lambda x: "y")

    area = CampBot().wiki.get_area(area_id=14273)
    area.save("Test")


def test_wiki(fix_requests, fix_input):
    from campbot import CampBot

    fix_input.set_response(lambda x: "y")

    route = CampBot().wiki.get_route(route_id=293549)
    route.is_personal()
    route.get_title("fr")

    xreport = CampBot().wiki.get_xreport(xreport_id=293549)
    xreport.is_personal()

    image = CampBot().wiki.get_image(image_id=1005116)
    image.is_personal()

    waypoint = CampBot().wiki.get_waypoint(waypoint_id=952999)
    waypoint.get_invalidity_reason()

    article = CampBot().wiki.get_article(article_id=1003911)
    article.is_personal()

    area = CampBot().wiki.get_area(area_id=14273)
    area.save("Test")

    CampBot().wiki.get_profile(profile_id=293549)
    CampBot().wiki.get_book(book_id=293549)
    CampBot().wiki.get_map(map_id=293549)

    list(CampBot().wiki.get_routes({}))
    list(CampBot().wiki.get_waypoints({}))
    list(CampBot().wiki.get_outings({}))
    list(CampBot().wiki.get_xreports({}))

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

    version = CampBot().wiki.get_wiki_object_version(293549, "r", "fr", 1738922)
    version.previous_version_id = None
    assert version.get_diff_url("fr") is not None

    route = CampBot().wiki.get_wiki_object(item_id=293549, document_type="r")
    assert route.get_url() == "https://www.camptocamp.org/routes/293549"
    assert (
        route.get_history_url("fr")
        == "https://www.camptocamp.org/routes/history/293549/fr"
    )

    CampBot().wiki.get_contributions(oldest_date="2017-12-12", newest_date="2017-12-13")

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

    class Contrib:
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
    from campbot import core, utils
    from campbot.__main__ import main_entry_point
    from docopt import DocoptExit

    utils.today()

    with pytest.raises(DocoptExit):
        main_entry_point()

    core._parse_filter("outings")
    core._parse_filter("outings#")
    core._parse_filter("outings#bbox=1%252C2%252C3%252C4")
    core._parse_filter("outings#act=viaferrata")
    core._parse_filter("outings?act=viaferrata")


def get_main_args(action, others=None):
    # noinspection PyDictCreation
    result = {
        "report_rc": False,
        "clean_rc": False,
        "contribs": False,
        "export": False,
        "clean": False,
        "report": False,
        "--delay": 0.01,
        "--login": "x",
        "--password": "y",
        "--lang": "fr",
        "--bbcode": True,
        "--batch": True,
        "<days>": "1",
        "<lang>": "fr",
        "<langs>": "fr,de",
        "<url>": "outings#u=286726",
        "<url_or_file>": "outings#u=286726",
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
    from campbot.checkers import get_fixed_tests, ReTest
    from campbot import CampBot
    from campbot.objects import Version, Contribution

    bot = CampBot()

    route = bot.wiki.get_route(123)
    waypoint = bot.wiki.get_waypoint(123)

    changes = (
        (
            Contribution(bot, {"user": {"user_id": 3199}, "document": {"type": "r"}}),
            Version(bot, {"document": route, "user": {}}),
            Version(bot, {"document": route, "user": {}}),
        ),
        (
            Contribution(bot, {"user": {"user_id": 3199}, "document": {"type": "w"}}),
            Version(bot, {"document": waypoint, "user": {}}),
            Version(bot, {"document": waypoint, "user": {}}),
        ),
    )

    for test in get_fixed_tests("fr"):
        for contrib, old_version, new_version in changes:
            test(contrib, old_version, Version(bot, {"document": None, "user": {}}))
            test(contrib, old_version, new_version)
            test(contrib, None, new_version)
            test(contrib, old_version, None)

    for contrib, old_version, new_version in changes:
        t = ReTest("x", "fr")
        t.patterns.append("e")
        t(contrib, old_version, new_version)


def test_weird(fix_requests, fix_input):
    from campbot import CampBot, __main__
    import os

    fix_input.set_response(lambda x: "n")

    bot = CampBot()

    obj = bot.wiki.get_article(123)
    obj.document_id = 1
    assert obj["document_id"] == 1
    assert obj.search(["xxx"], "fr") == False
    assert obj.save("test", True) is None

    user = bot.wiki.get_profile(123)
    assert user.get_last_contribution(newest_date="1970-01-01") is None

    obj = bot.wiki.get_waypoint(123)
    assert obj.get_invalidity_reason() == "elevation is missing"
    obj.elevation = 12
    assert obj.get_invalidity_reason() is None
    obj.waypoint_type = "hut"
    obj.custodianship = None
    assert obj.get_invalidity_reason() == "custodianship is missing"

    obj = bot.wiki.get_wiki_object(123, "o")
    assert obj.is_personal() == True

    os.environ["CAMPBOT_CREDENTIALS"] = "x@y"
    args = get_main_args("clean")
    args["--login"] = False
    __main__.main(args)

    with open("contributors.txt", "w") as f:
        f.write("666|1\n")
        f.write("667|1\n")
        f.write("667|100\n")
        f.write("668|100\n")
        f.write("123|1\n")

    bot.get_new_contributors()


def test_get_closest_documents(fix_requests):
    from campbot import CampBot, objects

    bot = CampBot()

    bot.find_closest_documents(objects.Waypoint, 289284, 6175526, 2000)


def test_get_voters(fix_requests):
    from campbot import CampBot, objects

    bot = CampBot()

    bot.forum.get_voters(1234, "poll", "option_id")
