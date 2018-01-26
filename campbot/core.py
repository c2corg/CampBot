# coding: utf-8

from __future__ import print_function, unicode_literals, division

import io
import requests
from datetime import datetime, timedelta
from dateutil import parser
from collections import OrderedDict
import pytz
import logging
import time
from requests.exceptions import HTTPError
import sys
from . import checkers
from . import objects

try:
    # py2
    # noinspection PyShadowingBuiltins
    input = raw_input
except NameError:
    # py3
    basestring = (str,)

__all__ = ['CampBot', 'WikiBot', 'ForumBot', 'BaseBot']


def today():
    return datetime.today()


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
        key = (url, str(kwargs))

        self._wait()
        logging.debug("GET %s", url)

        res = self._session.get(self.api_url + url,
                                proxies=self.proxies,
                                params=kwargs)

        res.raise_for_status()

        if res.headers['Content-type'].startswith('application/json'):
            return res.json()
        else:
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
    @property
    def ui_url(self):
        return self.api_url.replace("api", "www")

    def get_wiki_object_version(self, item_id, document_type, lang, version_id):
        if not version_id:
            return None

        constructor = objects.get_constructor(document_type)

        url = "/{}/{}/{}/{}"
        data = self.get(url.format(constructor.url_path, item_id, lang, version_id))

        return objects.Version(self.campbot, data)

    def get_wiki_object(self, item_id, constructor=None, document_type=None):
        if not constructor:
            constructor = objects.get_constructor(document_type)

        return constructor(self.campbot, self.get("/{}/{}".format(constructor.url_path, item_id)))

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

        oldest_date = kwargs.get("oldest_date", None) or today() + timedelta(days=-1)
        newest_date = kwargs.get("newest_date", None) or datetime.now()

        if isinstance(oldest_date, basestring):
            oldest_date = parser.parse(oldest_date)

        if isinstance(newest_date, basestring):
            newest_date = parser.parse(newest_date)

        user_id = kwargs.get("user_id", None)
        user_filter = "&u={}".format(user_id) if user_id else ""

        oldest_date = oldest_date.replace(tzinfo=pytz.UTC)
        newest_date = newest_date.replace(tzinfo=pytz.UTC)

        d = self.get("/documents/changes?limit=50" + user_filter)

        while True:
            for item in d["feed"]:
                written_at = parser.parse(item["written_at"])
                if written_at < oldest_date:
                    raise StopIteration

                if newest_date > written_at:
                    yield objects.Contribution(self.campbot, item)

            if "pagination_token" not in d:
                break

            pagination_token = d["pagination_token"]
            d = self.get("/documents/changes?limit=50&token=" + pagination_token + user_filter)

    def get_route_ids(self):
        return self.get_document_ids(objects.Route)

    def get_xreport_ids(self):
        return self.get_document_ids(objects.Xreport)

    def get_document_ids(self, constructor=None, document_type=None, filters=None):
        if not constructor:
            constructor = objects.get_constructor(document_type=document_type)

        for doc in self.get_documents_raw(constructor.url_path, filters=filters):
            yield doc["document_id"]

    def get_documents(self, constructor, filters=None):
        for doc in self.get_documents_raw(constructor.url_path, filters):
            yield constructor(self.campbot, doc)

    def get_documents_raw(self, url_path, filters=None):
        filters = filters or {}
        filters["offset"] = 0

        while True:
            filters_url = "&".join(["{}={}".format(k, v) for k, v in filters.items()])
            data = self.get("/{}?{}".format(url_path, filters_url))

            if len(data["documents"]) == 0:
                raise StopIteration

            for doc in data["documents"]:
                yield doc

            filters["offset"] += 30


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

    def unhide_posts(self, usernames):

        url = "/user_actions.json?offset={}&username={}&filter=5"

        for username in usernames.split(","):
            offset = 0
            while True:
                print(username, offset)

                d = self.get(url.format(offset, username))

                if len(d["user_actions"]) == 0:
                    break

                for action in d["user_actions"]:
                    if action["hidden"]:
                        print(username, action["post_id"], action["created_at"],
                              "{}/x/{}".format(self.api_url, action["topic_id"]))

                        self.put("/posts/{}/unhide".format(action["post_id"]), None)

                offset += 30


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

        oldest_date = today() - timedelta(days=180)

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

    def fix_markdown(self, processor, filename, ask_before_saving=True):

        logging.info("Fix markdown with {} processor".format(processor))
        logging.info("Ask before saving : {}".format(ask_before_saving))
        logging.info("Delay between each request : {}".format(self.wiki.min_delay))

        ids = {}
        with open(filename) as f:
            for line in f:
                line = line.replace(" ", "").replace("\n", "")
                item_id, item_type = line.split("|")
                constructor = objects.get_constructor(item_type)
                item_id = int(item_id)

                if item_id not in ids and (self.moderator or constructor not in (objects.Outing,
                                                                                 objects.WikiUser,
                                                                                 objects.Xreport)):
                    ids[item_id] = constructor
        i = 0
        for item_id, constructor in ids.items():
            i += 1

            item = self.wiki.get_wiki_object(item_id, constructor=constructor)

            url = "https://www.camptocamp.org/{}/{}".format(constructor.url_path, item_id)
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
                    # print(progress, "{} is impacted".format(url))
                    pass

                elif not ask_before_saving or input("Save {} y/[n]?".format(url)) == "y":
                    print(progress, "Saving {}".format(url))
                    try:
                        item.save(processor.comment)
                    except HTTPError as e:
                        print("Error while saving", url, e, file=sys.stderr)

                    print()
            else:
                print(progress, "Nothing found on {}".format(url))

    def export_outings(self, filters, filename=None):

        headers = ["date_start", "date_end", "title", "equipement_rating",
                   "global_rating", "height_diff_up", "rock_free_rating",
                   "condition_rating", "elevation_max", "img_count", "quality", "activities"]

        message = ";".join(["{" + h + "}" for h in headers]) + "\n"

        filters = {k: v for k, v in (v.split("=") for v in filters.split("&"))}

        with io.open(filename or "outings.csv", "w", encoding="utf-8") as f:
            f.write(message.format(**{h: h for h in headers}))
            for doc in self.wiki.get_documents(objects.Outing, filters):
                data = {h: doc.get(h, "") for h in headers}

                data["title"] = doc.get_title("fr").replace(";", ",")
                data["activities"] = ",".join(data["activities"])

                f.write(message.format(**data))

    def export_contributions(self, starts=None, ends=None, filename=None):

        message = ("{timestamp};{type};{document_id};{version_id};{document_version};"
                   "{title};{quality};{user};{lang}\n")

        with io.open(filename or "contributions.csv", "w", encoding="utf-8") as f:
            def write(**kwargs):
                f.write(message.format(**kwargs))

            write(timestamp="timestamp", type="type",
                  document_id="document_id", version_id="version_id", document_version="document_version",
                  title="title", quality="quality", user="username", lang="lang")

            for c in self.wiki.get_contributions(oldest_date=starts, newest_date=ends):
                write(timestamp=c.written_at,
                      type=c.document.url_path, document_id=c.document.document_id,
                      version_id=c.version_id, document_version=c.document.version,
                      title=c.document.title.replace(";", ","), quality=c.document.quality,
                      user=c.user.username, lang=c.lang)

    def check_recent_changes(self, check_message_url, lang):

        def get_version_length(version, lang):
            if not version:
                return 0

            locale = version.document.get_locale(lang)

            return locale.get_length() if locale else 0

        tests = checkers.get_fixed_tests(lang)
        tests += checkers.get_re_tests(self.forum.get_post(url=check_message_url), lang)

        messages = [
            "[Explications]({})\n".format(check_message_url),
            "[details=Signification des icônes]\n<table>",
            "<tr><th>Test</th><th>A relire</th><th>Corrigé</th></tr>",
        ]

        for test in tests:
            messages.append("<tr>")
            messages.append("<th>{}</th>".format(test.name))
            messages.append("<td>{}</td>".format(test.fail_marker))
            messages.append("<td>{}</td>".format(test.success_marker))
            messages.append("</tr>")

        messages.append("</table>\n[/details]\n\n----\n\n")

        items = OrderedDict()
        for contrib in self.wiki.get_contributions(oldest_date=datetime.now() - timedelta(days=1.3)):
            print(contrib.written_at, "get contrib")
            if contrib.lang == lang and contrib.document.type not in ("i", "o"):
                if contrib.document["document_id"] not in items:
                    items[contrib.document["document_id"]] = []

                items[contrib.document["document_id"]].append(contrib)

        for contribs in items.values():
            need_report = False
            report = []

            if len(contribs) != 1:
                report.append("* {} modifications ".format(
                    len(contribs),
                ))

            for contrib in contribs:
                print(contrib.written_at, "get doc")
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
                    old_is_ok, new_is_ok = test(contrib, old, new)

                    if old_is_ok and not new_is_ok:
                        emojis.append(test.fail_marker)
                        need_report = True
                    elif not old_is_ok and new_is_ok:
                        emojis.append(test.success_marker)

                delta = get_version_length(new, contrib.lang)
                delta -= get_version_length(old, contrib.lang)

                if delta < 0:
                    delta = "<del>{:+d}</del>".format(delta)
                elif delta > 0:
                    delta = "<ins>{:+d}</ins>".format(delta)
                else:
                    delta = "**=**"

                title = new.document.get_title(lang)

                report.append(
                    "{prefix}* {timestamp} {emojis} [{doc_title}]({doc_url}) "
                    "([{diff_title}]({diff_url}) | [hist]({hist_url})) "
                    "**·** ({delta}) **·** [{username}]({user_contrib_url})"
                    " →‎ *{comment}*".format(
                        prefix="" if len(contribs) == 1 else "  ",
                        timestamp=parser.parse(contrib.written_at).strftime("%H:%M"),
                        emojis="".join(emojis),
                        doc_title=title if len(title) else "*Vide*",
                        doc_url=new.document.get_url(lang),
                        diff_title="diff" if new.previous_version_id else "**new**",
                        diff_url=new.get_diff_url(lang),
                        hist_url=new.document.get_history_url(contrib.lang),
                        delta=delta,
                        username=contrib.user.name,
                        user_contrib_url=contrib.user.get_contributions_url(),
                        comment=contrib.comment if len(contrib.comment) else "&nbsp;"
                    )
                )

            if need_report:
                messages += report

        for m in messages:
            print(m)

        if len(messages) != 0:
            self.forum.post_message("\n".join(messages), check_message_url)
