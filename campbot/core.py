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
from . import objects
from campbot.processors import get_automatic_replacments

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
        self.min_delay = timedelta(seconds=float(min_delay or 3))

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

    def get_wiki_object(self, item_id, document_type=None, constructor=None):
        if not constructor:
            constructor = objects.get_constructor(document_type)

        return constructor(self.campbot, self.get("/{}/{}".format(constructor.url_path, item_id)))

    def get_article(self, article_id):
        return self.get_wiki_object(article_id, constructor=objects.Article)

    def get_route(self, route_id):
        return self.get_wiki_object(route_id, constructor=objects.Route)

    def get_waypoint(self, waypoint_id):
        return self.get_wiki_object(waypoint_id, constructor=objects.Waypoint)

    def get_profile(self, profile_id):
        return self.get_wiki_object(profile_id, constructor=objects.WikiUser)

    def get_area(self, area_id):
        return self.get_wiki_object(area_id, constructor=objects.Area)

    def get_image(self, image_id):
        return self.get_wiki_object(image_id, constructor=objects.Image)

    def get_book(self, book_id):
        return self.get_wiki_object(book_id, constructor=objects.Book)

    def get_map(self, map_id):
        return self.get_wiki_object(map_id, constructor=objects.Map)

    def get_xreport(self, xreport_id):
        return self.get_wiki_object(xreport_id, constructor=objects.Xreport)

    def get_route_ids(self, filters=None):
        return self.get_document_ids(filters=filters, constructor=objects.Route)

    def get_xreport_ids(self, filters=None):
        return self.get_document_ids(filters=filters, constructor=objects.Xreport)

    def get_document_ids(self, filters=None, document_type=None, constructor=None):
        if not constructor:
            constructor = objects.get_constructor(document_type=document_type)

        for doc in self.get_documents_raw(constructor.url_path, filters=filters):
            yield doc["document_id"]

    def get_routes(self, filters):
        return self.get_documents(constructor=objects.Route, filters=filters)

    def get_waypoints(self, filters):
        return self.get_documents(constructor=objects.Waypoint, filters=filters)

    def get_outings(self, filters):
        return self.get_documents(constructor=objects.Outing, filters=filters)

    def get_documents(self, filters=None, document_type=None, constructor=None):
        if not constructor:
            constructor = objects.get_constructor(document_type=document_type)

        for doc in self.get_documents_raw(constructor.url_path, filters):
            yield self.get_wiki_object(doc["document_id"], constructor=constructor)

    def get_documents_raw(self, url_path, filters=None):
        filters = filters or {}
        filters["offset"] = 0

        filters = {k: ",".join(map(str, v)) if isinstance(v, (list, set, tuple)) else v for k, v in filters.items()}

        while True:
            filters_url = "&".join(["{}={}".format(k, v) for k, v in filters.items()])
            data = self.get("/{}?{}".format(url_path, filters_url))

            if len(data["documents"]) == 0:
                raise StopIteration

            for doc in data["documents"]:
                yield doc

            filters["offset"] += 30

    def get_user(self, user_id=None, wiki_name=None, forum_name=None):
        if user_id:
            return objects.WikiUser(self.campbot, self.get("/profiles/{}".format(user_id)))

        name = wiki_name or forum_name

        data = self.get("/search?q={}&t=u&limit=50".format(name))

        prop = "name" if wiki_name else "forum_username"

        for item in data["users"]["documents"]:
            if item[prop] == name:
                return self.get_user(user_id=item["document_id"])

        raise Exception("Can't find user {}".format(wiki_name or forum_name))

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


class ForumBot(BaseBot):
    def get_last_message_timestamp(self, url, username):
        topic_id, _ = self._get_post_ids(url)
        data = self.get("/t/{}.json?username_filters={}".format(topic_id, username))
        return parser.parse(data["last_posted_at"])

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
    def __init__(self, proxies=None, min_delay=None, use_demo=False):

        domain = "camptocamp" if not use_demo else "demov6.camptocamp"

        self.wiki = WikiBot(self, "https://api.{}.org".format(domain),
                            proxies=proxies, min_delay=min_delay)

        self.forum = ForumBot(self, "https://forum.{}.org".format(domain),
                              proxies=proxies, min_delay=min_delay)

        self.moderator = False

        self.forum.headers['X-Requested-With'] = "XMLHttpRequest"
        self.forum.headers['Host'] = "forum.{}.org".format(domain)

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

        oldest_date = today() - timedelta(days=36500)
        newest_date = datetime(year=2018, month=2, day=18)

        last_contribs = {}
        ignored_voters = []

        def get_last_contrib(voter):
            if voter.username not in last_contribs:
                contributor = voter.get_wiki_user()

                last_contribs[voter.username] = contributor.get_last_contribution(
                    oldest_date=oldest_date,
                    newest_date=newest_date)

            return last_contribs[voter.username]

        polls = {}
        options = {}

        post = self.forum.get_post(url=url)

        for poll_name in post.polls:
            polls[poll_name] = {}
            for option in post.polls[poll_name].options:
                result = 0
                for voter in option.get_voters(post.id, poll_name):
                    if voter.username in allowed_members:
                        result += 1
                    else:
                        if False and get_last_contrib(voter) is None:
                            ignored_voters.append(voter.username)
                        else:
                            result += 1

                polls[poll_name][option.html] = result
                options[option.html] = 0

        sort_option = next(iter(options))

        print("<table><tr><th>Vote</th>")
        for option in options:
            print("<th>{}</th>".format(option))

        print("<th>Total</th></tr>")

        for poll_name, values in sorted(polls.items(),
                                        key=lambda item: item[1][sort_option],
                                        reverse=True):
            print("<tr><th>{}</th>".format(poll_name))
            total = 0
            for option in options:
                value = values.get(option, 0)
                print("<td>{}</td>".format(value))
                total += value

            print("<th>{}</th></tr>".format(total))

        print("</table>\n")

        if len(ignored_voters) != 0:
            ignored_voters = ["@{}".format(v) for v in ignored_voters]
            print("\n**Ignored votes** : {}".format(", ".join(set(ignored_voters))))

    def clean(self, url, ask_before_saving=True):
        constructor, filters = _parse_filter(url)
        processors = get_automatic_replacments(self)
        documents = self.wiki.get_documents(filters, constructor=constructor)

        self._process_documents(documents, processors, ask_before_saving)

    def _process_documents(self, documents, processors, ask_before_saving=True):

        for document in documents:

            if document.get("protected", False) and not self.moderator:
                print("{} is a protected".format(document.get_url()))

            elif "redirects_to" in document:
                pass  # document id is not available...

            elif not document.is_valid():
                print("{} : {}".format(document.get_url(), document.get_invalidity_reason()))

            else:
                messages = []
                must_save = False

                for processor in processors:
                    if processor.ready_for_production:
                        if processor(document):
                            messages.append(processor.comment)
                            must_save = True

                if must_save:
                    comment = ", ".join(messages)
                    try:
                        document.save(comment, ask_before_saving=ask_before_saving)
                    except Exception as e:
                        print("Error while saving {} :\n{}".format(document.get_url(), e))

    def export(self, url, filename=None):

        constructor, filters = _parse_filter(url)

        assert constructor is objects.Outing

        headers = ["date_start", "date_end", "title", "equipement_rating",
                   "global_rating", "height_diff_up", "rock_free_rating",
                   "condition_rating", "elevation_max", "img_count", "quality", "activities"]

        message = ";".join(["{" + h + "}" for h in headers]) + "\n"

        with io.open(filename or constructor.url_path + ".csv", "w", encoding="utf-8") as f:
            f.write(message.format(**{h: h for h in headers}))
            for raw in self.wiki.get_documents_raw(constructor.url_path, filters):
                doc = constructor(self, raw)
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

    def get_modified_documents(self, lang, oldest_date=None, excluded_users=()):
        result = OrderedDict()
        for contrib in self.wiki.get_contributions(oldest_date=oldest_date):
            if contrib.lang == lang and \
                    contrib.document.type not in ("i", "o", "x") and \
                    contrib.user.name not in excluded_users:

                key = (contrib.document["document_id"], contrib.document.type)
                if key not in result:
                    result[key] = []

                result[key].append(contrib)

        return result

    def fix_recent_changes(self, oldest_date, lang, ask_before_saving):

        excluded_ids = [996571, ]

        processors = get_automatic_replacments(self)

        def get_documents():

            for document_id, document_type in self.get_modified_documents(lang, oldest_date,
                                                                          ("rabot", "robot.topoguide", "botopo")):

                document = self.wiki.get_wiki_object(document_id, document_type=document_type)

                if document_id not in excluded_ids:
                    yield document

        print("Fix recent changes")
        self._process_documents(get_documents(), processors, ask_before_saving)
        print("Fix recent changes finished")


def _parse_filter(url):
    url = url.replace("https://www.camptocamp.org/", "")

    document_type, filters = url.split("#", 1)
    filters = {k: v for k, v in (v.split("=") for v in filters.split("&"))}

    for key in filters:
        if key == "bbox":
            filters[key] = filters[key].replace("%252C", "%2C")
        elif key in ("act", "rock_type"):
            filters[key] = filters[key].replace("%252C", ",")

    constructor = {
        "profiles": objects.WikiUser,
        "area": objects.Area,
        "waypoints": objects.Waypoint,
        "outings": objects.Outing,
        "images": objects.Image,
        "map": objects.Map,
        "xreports": objects.Xreport,
        "articles": objects.Article,
        "books": objects.Book,
        "routes": objects.Route
    }[document_type]

    return constructor, filters
