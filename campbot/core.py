from __future__ import print_function, unicode_literals, division

import requests
from datetime import datetime, timedelta
from dateutil import parser
from collections import OrderedDict
import pytz
import logging
import time
from requests.exceptions import HTTPError
import sys

from . import objects

try:
    input = raw_input
except NameError:
    pass

__all__ = ['CampBot', 'WikiBot', 'ForumBot', 'BaseBot']


class UserInterrupt(BaseException):
    pass


class BaseBot(object):
    min_delay = timedelta(seconds=1)

    def __init__(self, campbot, api_url, proxies=None, min_delay=None):
        self.campbot = campbot
        self.api_url = api_url
        self._session = requests.Session()
        self.proxies = proxies
        self._next_request_datetime = datetime.now()
        self.min_delay = timedelta(seconds=float(min_delay or 1))

    @property
    def headers(self):
        return self._session.headers

    def _wait(self):
        to_wait = (self._next_request_datetime - datetime.now()).total_seconds()

        if to_wait > 0:
            time.sleep(to_wait)

        self._next_request_datetime = datetime.now() + self.min_delay

    def get(self, url, **kwargs):
        self._wait()
        logging.debug("GET %s", url)

        res = self._session.get(self.api_url + url,
                                proxies=self.proxies,
                                params=kwargs)

        res.raise_for_status()

        if res.headers['Content-type'].startswith('application/json'):
            return res.json()

        return res.content

    def post(self, url, data):
        self._wait()
        logging.debug("POST %s", url)

        res = self._session.post(self.api_url + url, json=data, proxies=self.proxies)

        res.raise_for_status()

        if res.headers['Content-type'].startswith('application/json'):
            return res.json()

        return res.content

    def put(self, url, data):
        self._wait()
        logging.debug("POST %s", url)

        res = self._session.put(self.api_url + url, json=data,
                                proxies=self.proxies)

        res.raise_for_status()

        if res.headers['Content-type'].startswith('application/json'):
            return res.json()

        return res.content


class WikiBot(BaseBot):
    def get_wiki_object_version(self, id, document_type, lang, version_id):
        if not version_id:
            return None

        constructor = objects.get_constructor(document_type)

        url = "/{}/{}/{}/{}"
        data = self.get(url.format(constructor.url_path, id, lang, version_id))

        return objects.Version(self.campbot, data)

    def get_wiki_object(self, id, constructor=None, document_type=None):
        if not constructor:
            constructor = objects.get_constructor(document_type)

        return constructor(self.campbot, self.get("/{}/{}".format(constructor.url_path, id)))

    def get_route(self, route_id):
        return self.get_wiki_object(route_id, constructor=objects.Route)

    def get_waypoint(self, waypoint_id):
        return self.get_wiki_object(waypoint_id, constructor=objects.Waypoint)

    def get_user(self, user_id=None, wiki_name=None, forum_name=None):
        if user_id:
            return objects.WikiUser(self.campbot, self.get("/profiles/{}".format(user_id)))

        name = wiki_name or forum_name

        data = self.get("/search?q={}&t=u&limit=50".format(name))

        prop = "name" if wiki_name else "forum_username"

        for item in data["users"]["documents"]:
            if item[prop] == name:
                return self.get_user(user_id=item["document_id"])

        return None

    def get_contributions(self, **kwargs):

        oldest_date = kwargs.get("oldest_date", None) or datetime.today() + timedelta(days=-1)
        newest_date = kwargs.get("newest_date", None) or datetime.now()
        user_id = kwargs.get("user_id", None)
        user_filter = "&u={}".format(user_id) if user_id else ""

        oldest_date = oldest_date.replace(tzinfo=pytz.UTC)
        newest_date = newest_date.replace(tzinfo=pytz.UTC)

        d = self.get("/documents/changes?limit=50" + user_filter)
        while True:
            for item in d["feed"]:
                written_at = parser.parse(item["written_at"])
                if oldest_date > written_at:
                    raise StopIteration

                if newest_date > written_at:
                    yield objects.Contribution(self.campbot, item)

            if "pagination_token" not in d:
                break

            pagination_token = d["pagination_token"]
            d = self.get("/documents/changes?limit=50&token=" + pagination_token + user_filter)

    def get_route_ids(self):
        offset = 0

        while True:
            data = self.get("/routes?offset={}".format(offset))
            for route in data["documents"]:
                yield route["document_id"]

            offset += 50


class ForumBot(BaseBot):
    def post_message(self, message, url):
        topic_id, _ = self._get_post_ids(url)
        self.post("/posts", {"topic_id": topic_id, "raw": message})

    def get_group_members(self, group_name):
        result = []

        expected_len = 1
        while len(result) < expected_len:
            data = self.get("/groups/{}/members.json?limit=50&offset={}".format(group_name, len(result)))
            expected_len = data["meta"]["total"]
            result += data["members"]

        return [objects.ForumUser(self.campbot, user) for user in result]

    def _get_post_ids(self, url):
        url = url.replace(self.api_url, "").split("?")[0].split("/")
        assert url[1] == 't'
        topic_id = url[3]
        post_number = int(url[4]) if len(url) >= 5 else 1

        return topic_id, post_number

    def get_topic(self, topic_id=None, url=None):
        if url:
            topic_id, _ = self._get_post_ids(url)

        return self.get("/t/{}.json".format(topic_id))

    def get_post(self, topic_id=None, post_number=None, url=None):
        if url:
            topic_id, post_number = self._get_post_ids(url)

        topic = self.get_topic(topic_id)
        post_id = topic["post_stream"]["stream"][post_number - 1]

        return objects.Post(self.campbot, self.get("/posts/{}.json".format(post_id)))

    def get_participants(self, url):
        topic = self.get_topic(url=url)
        return topic["details"]["participants"]


class CampBot(object):
    def __init__(self, proxies=None, min_delay=None):
        self.wiki = WikiBot(self, "https://api.camptocamp.org", proxies=proxies, min_delay=min_delay)
        self.forum = ForumBot(self, "https://forum.camptocamp.org", proxies=proxies, min_delay=min_delay)
        self.moderator = False
        self.forum.headers['X-Requested-With'] = "XMLHttpRequest"
        self.forum.headers['Host'] = "forum.camptocamp.org"

    def login(self, login, password):
        res = self.wiki.post("/users/login", {"username": login, "password": password, "discourse": True})
        token = res["token"]
        self.moderator = "moderator" in res["roles"]
        self.wiki.headers["Authorization"] = 'JWT token="{}"'.format(token)
        self.forum.get(res["redirect_internal"].replace(self.forum.api_url, ""))
        self.forum.headers['X-CSRF-Token'] = self.forum.get("/session/csrf")["csrf"]

    def check_voters(self, url, allowed_groups=()):

        allowed_members = []
        for group in allowed_groups:
            allowed_members += self.forum.get_group_members(group)

        allowed_members = {u.username: u for u in allowed_members}

        oldest_date = datetime.today() - timedelta(days=180)

        post = self.forum.get_post(url=url)
        for poll_name in post.polls:
            for option in post.polls[poll_name].options:
                print(poll_name, option.html, "has", option.votes, "voters : ")
                for voter in option.get_voters(post.id, poll_name):
                    if voter.username in allowed_members:
                        print("    ", voter.username, "is allowed")
                    else:
                        contributor = voter.get_wiki_user()
                        last_contribution = contributor.get_last_contribution(oldest_date=oldest_date)
                        if not last_contribution:
                            print("    ", voter.username, "has no contribution")
                        else:
                            print("    ", voter.username, last_contribution["written_at"])

            print()

    def fix_markdown(self, processor, ask_before_saving=True,
                     route_ids=None, waypoint_ids=None, area_ids=None,
                     user_ids=None, image_ids=None, outing_ids=None,
                     xreport_ids=None, article_ids=None, book_ids=None):

        logging.info("Fix markdown with {} processor".format(processor))
        logging.info("Ask before saving : {}".format(ask_before_saving))
        logging.info("Delay between each request : {}".format(self.wiki.min_delay))

        lists = [
            (route_ids, objects.Route),
            (waypoint_ids, objects.Waypoint),
            (article_ids, objects.Article),
            (image_ids, objects.Image),
            (book_ids, objects.Book),
            (area_ids, objects.Area)
        ]

        if self.moderator:
            lists += [(outing_ids, objects.Outing),
                      (user_ids, objects.WikiUser),
                      (xreport_ids, objects.Xreport)]

        for ids, constructor in lists:
            if ids and len(ids) != 0:
                for id, i in zip(ids, range(len(ids))):
                    item = self.wiki.get_wiki_object(id, constructor=constructor)

                    url = "https://www.camptocamp.org/{}/{}".format(constructor.url_path, id)
                    progress = "{}/{}".format(i + 1, len(ids))

                    if "redirects_to" in item:
                        print(progress, "{} is a redirection".format(url))

                    elif processor.ready_for_production and \
                            not self.moderator and \
                            (item.protected or item.is_personal()):
                        print(progress, "{} is protected".format(url))

                    elif not item.is_valid():
                        print(progress, "{} : {}".format(url, item.get_invalidity_reason()))

                    elif item.fix_markdown(processor):
                        if not processor.ready_for_production:
                            print(progress, "{} is impacted".format(url))

                        elif not ask_before_saving or input("Save {} y/[n]?".format(url)) == "y":
                            print(progress, "Saving {}".format(url))
                            try:
                                item.save(processor.comment)
                            except HTTPError as e:
                                print("Error while saving", url, e, file=sys.stderr)

                            print()
                    else:
                        print(progress, "Nothing found on {}".format(url))

    def check_recent_changes(self, check_message_url, lang):

        class LengthTest(object):
            def __init__(self):
                self.name = "Document size"

                self.fail_marker = emoji("/images/emoji/apple/rage.png?v=3", self.name)
                self.success_marker = ""

            def __call__(self, old_version, new_version):
                old_doc = old_version.document if old_version else None
                new_doc = new_version.document if new_version else None

                if not old_doc or "redirects_to" in old_doc:
                    return True, True

                if not new_doc or "redirects_to" in new_doc:
                    return True, True

                result = True

                old_locale_length = old_doc.get_locale(lang).get_length()
                new_locale_length = new_doc.get_locale(lang).get_length()

                if old_locale_length != 0 and new_locale_length / old_locale_length < 0.5:
                    result = False

                return True, result

        class ReTest(object):
            def __init__(self, name):
                self.name = name
                self.patterns = []
                self.fail_marker = emoji("/images/emoji/apple/red_circle.png?v=3", self.name)
                self.success_marker = emoji("/images/emoji/apple/white_check_mark.png?v=3",
                                            self.name + " is now correct")

            def __call__(self, old_version, new_version):
                old_doc = old_version.document if old_version else None
                new_doc = new_version.document if new_version else None

                def test(doc):
                    if not doc or "redirects_to" in doc:
                        return True

                    return not doc.search(self.patterns, lang)

                return test(old_doc), test(new_doc)

        class HistoryTest(object):
            activities_with_history = ["snow_ice_mixed", "mountain_climbing", "rock_climbing", "ice_climbing"]

            def __init__(self):
                self.name = "History"
                self.fail_marker = emoji("/images/emoji/apple/closed_book.png?v=3", self.name)
                self.success_marker = emoji("/images/emoji/apple/green_book.png?v=3", self.name + " is now correct")

            def __call__(self, old_version, new_version):
                old_doc = old_version.document if old_version else None
                new_doc = new_version.document if new_version else None

                def test(doc):
                    if not doc or "redirects_to" in doc or doc.type != "r":
                        return True

                    if len([act for act in doc.activities if act in self.activities_with_history]) == 0:
                        return True

                    locale = doc.get_locale(lang)
                    if locale and (not locale.route_history or len(locale.route_history) == 0):
                        return False

                    return True

                return test(old_doc), test(new_doc)

        def doc_link(doc, lang=None):
            title = doc.get_locale(lang).get_title()
            title = title if len(title) else "*Vide*"

            return "[{}](https://www.camptocamp.org{})".format(
                title,
                doc.get_url(lang),
            )

        def user_link(user):
            return "[{}](https://www.camptocamp.org/whatsnew#u={})".format(user["name"], user["user_id"])

        def hist_link(doc, lang):
            return "[hist](https://www.camptocamp.org/routes/history/{}/{})".format(doc.document_id, lang)

        def diff_link(version, lang):
            if not version.previous_version_id:
                return "**New**"

            return "[diff]({})".format(version.get_diff_url(lang))

        def emoji(src, text):
            return '<img src="{}" class="emoji" title="{}" alt="{}">'.format(src, text, text)

        tests = [HistoryTest(), LengthTest()]

        post = self.forum.get_post(url=check_message_url)
        test = None
        for line in post.raw.split("\n"):
            if line.startswith("#"):
                test = ReTest(line)
                tests.append(test)
            elif line.startswith("    ") and test:
                pattern = line[4:]
                if len(pattern.strip()) != 0:
                    test.patterns.append(line[4:])

        messages = []

        items = OrderedDict()
        for contrib in self.wiki.get_contributions():
            if contrib.lang == lang:
                if contrib.document["document_id"] not in items:
                    items[contrib.document["document_id"]] = (contrib.get_full_document(), [])

                items[contrib.document["document_id"]][1].append(contrib)

        for doc, contribs in items.values():
            need_report = False
            report = []

            if len(contribs) != 1:
                report.append("* {} modifications ".format(
                    len(contribs),
                ))

            for contrib in contribs:
                new = self.wiki.get_wiki_object_version(contrib.document.document_id,
                                                        contrib.document.type,
                                                        contrib.lang,
                                                        contrib.version_id)

                old = self.wiki.get_wiki_object_version(contrib.document.document_id,
                                                        contrib.document.type,
                                                        contrib.lang,
                                                        new.previous_version_id)

                emojis = []

                for test in tests:
                    old_is_ok, new_is_ok = test(old, new)

                    if old_is_ok and not new_is_ok:
                        emojis.append(test.fail_marker)
                        need_report = True
                    elif not old_is_ok and new_is_ok:
                        emojis.append(test.success_marker)

                delta = new.document.get_locale(contrib.lang).get_length()
                delta -= old.document.get_locale(contrib.lang).get_length() if old else 0

                if delta < 0:
                    delta = "<del>{:+d}</del>".format(delta)
                elif delta > 0:
                    delta = "<ins>{:+d}</ins>".format(delta)
                else:
                    delta = "**=**"

                report.append("{}* {} {} {} ({} | {}) **·** ({}) **·** {} →‎ *{}*".format(
                    "" if len(contribs) == 1 else "  ",
                    parser.parse(contrib.written_at).strftime("%H:%M"),
                    "".join(emojis),
                    doc_link(new.document, contrib.lang),
                    diff_link(new, contrib.lang),
                    hist_link(new.document, contrib.lang),
                    delta,
                    user_link(contrib.user),
                    contrib.comment if len(contrib.comment) else "&nbsp;"
                ))

            if need_report:
                messages += report

        if len(messages) != 0:

            for m in messages:
                print(m)

                #  self.forum.post_message("\n".join(messages), check_message_url)
