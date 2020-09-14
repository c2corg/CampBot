# coding: utf-8

from __future__ import print_function, unicode_literals, division

import os
import io
import requests
from datetime import datetime, timedelta
from dateutil import parser
from collections import OrderedDict
import pytz
import logging
import time
from . import utils
from . import objects
from campbot.processors import get_automatic_replacments
from campbot.checkers import get_document_tests

try:
    # py2
    # noinspection PyShadowingBuiltins
    input = raw_input
except NameError:
    # py3
    basestring = (str,)

__all__ = ["CampBot", "WikiBot", "ForumBot", "BaseBot"]


class UserInterrupt(BaseException):
    pass


class BaseBot(object):
    min_delay = timedelta(seconds=3)

    def __init__(self, campbot, api_url, proxies=None, min_delay=None):
        self.campbot = campbot
        self.api_url = api_url
        self._session = requests.Session()
        self.proxies = proxies
        self._next_request_datetime = datetime.now()
        if min_delay is not None:
            self.min_delay = timedelta(seconds=float(min_delay))

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

        res = self._session.get(self.api_url + url, proxies=self.proxies, params=kwargs)

        res.raise_for_status()

        if res.headers["Content-type"].startswith("application/json"):
            return res.json()
        else:
            return res.content

    def post(self, url, data):
        self._wait()
        logging.debug("POST %s", url)

        res = self._session.post(self.api_url + url, json=data, proxies=self.proxies)

        res.raise_for_status()

        assert res.headers["Content-type"].startswith("application/json")

        return res.json()

    def put(self, url, data):
        self._wait()
        logging.debug("POST %s", url)

        res = self._session.put(self.api_url + url, json=data, proxies=self.proxies)

        res.raise_for_status()

        assert res.headers["Content-type"].startswith("application/json")

        return res.json()


class WikiBot(BaseBot):
    """
        Get functions for all camptocamp.org wiki
    """

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
        """
        Return a wiki object. You must specify document_type OR constructor

        :param item_id: numerical document id
        :param document_type: type letter ('r' for route, 'w' for waypoint...)
        :param constructor: objects.Route, objects.Waypoint...

        :return: a wiki object
        """
        if not constructor:
            constructor = objects.get_constructor(document_type)

        return constructor(
            self.campbot, self.get("/{}/{}".format(constructor.url_path, item_id))
        )

    def get_article(self, article_id):
        """
        Get article object

        :param article_id: article numerical id
        :return: article object
        """

        return self.get_wiki_object(article_id, constructor=objects.Article)

    def get_route(self, route_id):
        """
        Get route object

        :param route_id: route numerical id
        :return: route object
        """

        return self.get_wiki_object(route_id, constructor=objects.Route)

    def get_waypoint(self, waypoint_id):
        """
        Get waypoint object

        :param waypoint_id: waypoint numerical id
        :return:  waypoint object
        """

        return self.get_wiki_object(waypoint_id, constructor=objects.Waypoint)

    def get_profile(self, profile_id):
        return self.get_wiki_object(profile_id, constructor=objects.WikiUser)

    def get_outing(self, outing_id):
        return self.get_wiki_object(outing_id, constructor=objects.Outing)

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

    def get_document_versions(self, document_id, lang):
        return self.get("/document/{}/history/{}".format(document_id, lang))

    def get_route_ids(self, filters=None):
        return self.get_document_ids(filters=filters, constructor=objects.Route)

    def get_outing_ids(self, filters=None):
        return self.get_document_ids(filters=filters, constructor=objects.Outing)

    def get_xreport_ids(self, filters=None):
        return self.get_document_ids(filters=filters, constructor=objects.Xreport)

    def get_document_ids(self, filters=None, document_type=None, constructor=None):
        if not constructor:
            constructor = objects.get_constructor(document_type=document_type)

        for doc in self.get_documents_raw(constructor.url_path, filters=filters):
            yield doc["document_id"]

    def get_routes(self, filters):
        """
        Get list of route. This function is a generator.

        :param filters: key-value dictionary
        :return: generator of route objects
        """

        return self.get_documents(constructor=objects.Route, filters=filters)

    def get_waypoints(self, filters):
        return self.get_documents(constructor=objects.Waypoint, filters=filters)

    def get_outings(self, filters):
        return self.get_documents(constructor=objects.Outing, filters=filters)

    def get_xreports(self, filters):
        return self.get_documents(constructor=objects.Xreport, filters=filters)

    def get_documents(self, filters=None, document_type=None, constructor=None):
        """
        Return a list of wiki objects, this function is a generator

        :param filters: a key-value dictionary
        :param document_type: type letter, like 'a', 'r', 'w'...
        :param constructor: objects.Area, objects.Route ...
        """
        if not constructor:
            constructor = objects.get_constructor(document_type=document_type)

        for doc in self.get_documents_raw(constructor.url_path, filters):
            yield self.get_wiki_object(doc["document_id"], constructor=constructor)

    def get_documents_raw(self, url_path, filters=None):
        filters = filters or {}
        filters["offset"] = 0

        filters = {
            k: ",".join(map(str, v)) if isinstance(v, (list, set, tuple)) else v
            for k, v in filters.items()
        }

        while True:
            filters_url = "&".join(["{}={}".format(k, v) for k, v in filters.items()])
            url = "/{}?{}".format(url_path, filters_url)
            print(url)
            data = self.get(url)

            if len(data["documents"]) == 0:
                return

            for doc in data["documents"]:
                yield doc

            filters["offset"] += 30

    def get_user(self, user_id=None, wiki_name=None, forum_name=None):
        if user_id:
            return objects.WikiUser(
                self.campbot, self.get("/profiles/{}".format(user_id))
            )

        name = wiki_name or forum_name

        data = self.get("/search?q={}&t=u&limit=50".format(name))

        prop = "name" if wiki_name else "forum_username"

        for item in data["users"]["documents"]:
            if item[prop] == name:
                return self.get_user(user_id=item["document_id"])

        raise Exception("Can't find user {}".format(wiki_name or forum_name))

    def get_contributions(self, **kwargs):

        oldest_date = kwargs.get("oldest_date", None) or utils.today() + timedelta(
            days=-1
        )
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
                    return

                if newest_date > written_at:
                    yield objects.Contribution(self.campbot, item)

            if "pagination_token" not in d:
                break

            pagination_token = d["pagination_token"]
            d = self.get(
                "/documents/changes?limit=50&token=" + pagination_token + user_filter
            )


class ForumBot(BaseBot):
    def post_message(self, message, url):
        """
        post a message into an existant forum thread

        :param message: message content
        :param url: thread URL
        """

        topic_id, _ = self._get_post_ids(url)
        self.post("/posts", {"topic_id": topic_id, "raw": message})

    def get_group_members(self, group_name):
        """
        Get all group members

        :param group_name: example : "Association"

        :return: list of forum username
        """
        result = []

        expected_len = 1
        while len(result) < expected_len:
            data = self.get(
                "/groups/{}/members.json?limit=50&offset={}".format(
                    group_name, len(result)
                )
            )
            expected_len = data["meta"]["total"]
            result += data["members"]

        return [objects.ForumUser(self.campbot, user) for user in result]

    def add_users_to_group(self, group_name, users):
        for user in users:
            assert not user.startswith("@"), "Please provide names without trailing @"

        group = self.get("/groups/{}.json".format(group_name))

        data = {"usernames": ",".join(users)}
        self.put("/groups/{}/members.json".format(group["basic_group"]["id"]), data)

    def _get_post_ids(self, url):
        url = url.replace(self.api_url, "").split("?")[0].split("/")
        assert url[1] == "t"
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

    def get_voters(self, post_id, poll_name, option_id):
        """Return the complete list of voters for a given option on a forum poll"""
        page = 1

        result = []

        while True:
            temp = self.get(
                "/polls/voters.json?post_id={}&poll_name={}&option_id={}&page={}".format(
                    post_id, poll_name, option_id, page
                )
            )

            if len(temp["voters"][option_id]) == 0:
                break

            result += temp["voters"][option_id]

            page += 1

        return result

    def get_participants(self, url):
        topic = self.get_topic(url=url)
        return topic["details"]["participants"]


class CampBot(object):
    """
    CampBot() object is the main class. You must instanciate only one instance of it.
    It contains two property : 

    * ``wiki`` for interacting with camptocamp.org wiki
    * ``forum`` for interacting with camptocamp.org forum
    """

    def __init__(self, min_delay=None, proxies=None, use_demo=False):
        """
            :param min_delay: in seconds, minimum delay between each request
            :param proxies: key-url dictionary
            :param use_demo: Boolean, True if you want to use C2C demo API
    
            :Example:
    
            >>> bot = CampBot(min_delay=10, proxies={"https": "https://login:password@proxy.com"})
            
        """

        domain = "camptocamp" if not use_demo else "demov6.camptocamp"

        self.wiki = WikiBot(
            self,
            "https://api.{}.org".format(domain),
            proxies=proxies,
            min_delay=min_delay,
        )
        """WikiBot instance"""

        self.forum = ForumBot(
            self,
            "https://forum.{}.org".format(domain),
            proxies=proxies,
            min_delay=min_delay,
        )

        """ForumBot instance"""

        self.moderator = False
        """True if logged with a moderator account"""

        self.forum.headers["X-Requested-With"] = "XMLHttpRequest"
        self.forum.headers["Host"] = "forum.{}.org".format(domain)

    def login(self, login, password):
        """
            Login to camptocamp.org, mandatory for write actions. 
            It also sign-in to forum. 

            :param login: bot login used to sign-in (not the numerical ID)
            :param password: bot password
            
        """

        res = self.wiki.post(
            "/users/login", {"username": login, "password": password, "discourse": True}
        )
        token = res["token"]
        self.moderator = "moderator" in res["roles"]
        self.wiki.headers["Authorization"] = 'JWT token="{}"'.format(token)
        self.forum.get(res["redirect_internal"].replace(self.forum.api_url, ""))
        self.forum.headers["X-CSRF-Token"] = self.forum.get("/session/csrf")["csrf"]

    def get_documents(self, url_or_filename):
        """
        Get a generator of document, given a filename or a URL.

        :param url_or_filename:
        :return: generator
        """
        if os.path.isfile(url_or_filename):
            return self._get_documents_from_file(url_or_filename)

        return self._get_documents_from_url(url_or_filename)

    def _get_documents_from_file(self, filename):
        """
        Get a generator of document, given a file.
        The file must contains one id/type per line, separated by a pipe.

        :param filename:
        :return: generator
        """
        with open(filename, "r") as f:
            for line in f:
                item_id, item_type = (
                    line.replace(" ", "").replace("\n", "").replace("\r", "").split("|")
                )
                item_id = int(item_id)

                try:
                    yield self.wiki.get_wiki_object(item_id, item_type)
                except requests.HTTPError as e:  # pragma: no cover
                    print("{error}, item skipped".format(error=e))

    def _get_documents_from_url(self, url):
        """
        Get a generator of document, given a camptocamp url

        :param url: camptocamp url, or shorthand like routes#w=123
        :return: generator
        """
        constructor, filters = _parse_filter(url)
        return self.wiki.get_documents(filters, constructor=constructor)

    def clean(self, url_or_filename, langs, ask_before_saving=True, clean_bbcode=False):
        """
            Clean a set of document.

            :param url_or_filename: Camptocamp.org URL, or filename
            :param langs: comma-separated list of lang identifiers
            :param ask_before_saving: Boolean
            :param clean_bbcode: Boolean

        """

        assert len(langs) != 0

        documents = self.get_documents(url_or_filename)
        processors = get_automatic_replacments(self, clean_bbcode)

        self._process_documents(
            documents, processors, langs, ask_before_saving, excluded_ids=[996571,]
        )

    def report(self, url_or_filename, lang):
        """
            Make quality report on a set of document.

            :param url_or_filename: Camptocamp.org URL, or filename
            :param langs: comma-separated list of lang identifiers
        """

        documents = [d for d in self.get_documents(url_or_filename)]

        tests = get_document_tests(lang)
        forum_report = []
        stdout_report = []

        for test in tests:
            failing_docs = []
            for document in documents:
                if "redirects_to" in document:
                    pass  # document id is not available...
                elif not test.test_document(document):
                    failing_docs.append(document)

            if len(failing_docs) != 0:
                stdout_report.append(test.name)
                forum_report.append("* {}".format(test.name))

                failing_docs.sort(key=lambda d: d.get_title(lang))

                for document in failing_docs:
                    url = document.get_url()
                    title = document.get_title(lang)

                    stdout_report.append("    {}\t {}".format(url, title))
                    forum_report.append("  * [{}]({})".format(title, url))

        print("\n".join(stdout_report))

    def _process_documents(
        self, documents, processors, langs, ask_before_saving=True, excluded_ids=None
    ):

        for document in documents:

            if "redirects_to" in document:
                pass  # document id is not available...

            elif excluded_ids is not None and document.document_id in excluded_ids:
                pass

            elif document.get("protected", False) and not self.moderator:
                print("{} is a protected".format(document.get_url()))

            elif document.is_personal() and not self.moderator:
                print("{} is a personal".format(document.get_url()))

            elif not document.is_valid():
                print(
                    "{} : {}".format(
                        document.get_url(), document.get_invalidity_reason()
                    )
                )

            else:
                messages = []
                must_save = False

                for processor in processors:
                    if processor.ready_for_production:
                        if processor(document, langs):
                            messages.append(processor.comment)
                            must_save = True

                if must_save:
                    comment = ", ".join(messages)
                    try:
                        document.save(comment, ask_before_saving=ask_before_saving)
                    except Exception as e:
                        print(
                            "Error while saving {} :\n{}".format(document.get_url(), e)
                        )

    def export(self, url, filename=None):
        """
            Export all document given by a camptocamp.org url

            :param url: Camptocamp.org URL
            :param filename: Output file name. Defaut : <document_type>.csv

        """

        constructor, filters = _parse_filter(url)

        headers = [
            "document_id",
            "title",
            "url",
            "activities",
            "available_langs",
            "user_name",
            "user_id",
        ]

        data = []
        for raw in self.wiki.get_documents_raw(constructor.url_path, filters):
            for key in raw:
                if key not in headers and isinstance(raw[key], (str, bool, int, float)):
                    headers.append(key)

            item = {h: raw.get(h, "") or "" for h in headers}
            doc = constructor(self, raw)
            item["title"] = doc.get_title("fr").replace(";", ",")
            item["url"] = doc.get_url()
            item["activities"] = ",".join(sorted(item["activities"] or []))
            item["available_langs"] = ",".join(sorted(item["available_langs"] or []))
            item["user_id"] = raw.get("author", {"user_id": ""})["user_id"]
            item["user_name"] = raw.get("author", {"name": ""})["name"]

            data.append(item)

        message = ";".join(["{" + h + "}" for h in headers]) + "\n"

        with io.open(
            filename or constructor.url_path + ".csv", "w", encoding="utf-8"
        ) as f:
            f.write(message.format(**{h: h for h in headers}))
            for item in data:
                f.write(message.format(**{h: item.get(h, "") for h in headers}))

    def export_contributions(self, starts=None, ends=None, filename=None):
        """
            Export all document given by a camptocamp.org url

            :param starts: Start date, default is now minus 24 hours
            :param ends: default is now
            :param filename: Output file name. Defaut : contributions.csv

        """

        message = (
            "{timestamp};{type};{document_id};{version_id};{document_version};"
            "{title};{quality};{user};{lang}\n"
        )

        with io.open(filename or "contributions.csv", "w", encoding="utf-8") as f:

            def write(**kwargs):
                f.write(message.format(**kwargs))

            write(
                timestamp="timestamp",
                type="type",
                document_id="document_id",
                version_id="version_id",
                document_version="document_version",
                title="title",
                quality="quality",
                user="username",
                lang="lang",
            )

            for c in self.wiki.get_contributions(oldest_date=starts, newest_date=ends):
                write(
                    timestamp=c.written_at,
                    type=c.document.url_path,
                    document_id=c.document.document_id,
                    version_id=c.version_id,
                    document_version=c.document.version,
                    title=c.document.title.replace(";", ","),
                    quality=c.document.quality,
                    user=c.user.username,
                    lang=c.lang,
                )

    def get_modified_documents(
        self, lang, oldest_date=None, newest_date=None, excluded_users=()
    ):
        result = OrderedDict()
        for contrib in self.wiki.get_contributions(
            oldest_date=oldest_date, newest_date=newest_date
        ):
            if (
                contrib.lang == lang
                and contrib.document.type not in ("i", "o", "x")
                and contrib.document.type != "m"
                and contrib.user.name not in excluded_users
            ):

                key = (contrib.document["document_id"], contrib.document.type)
                if key not in result:
                    result[key] = []

                result[key].append(contrib)

        return result

    def clean_recent_changes(self, days, lang, ask_before_saving):
        newest_date = utils.today().replace(hour=0, minute=0, second=0, microsecond=0)
        oldest_date = newest_date - timedelta(days=days)

        excluded_ids = [
            996571,
        ]

        processors = get_automatic_replacments(self)

        def get_documents():

            for document_id, document_type in self.get_modified_documents(
                lang,
                oldest_date,
                newest_date,
                ("rabot", "robot.topoguide", "botopo", "CaBot"),
            ):

                document = self.wiki.get_wiki_object(
                    document_id, document_type=document_type
                )

                if document_id not in excluded_ids:
                    yield document

        print("Fix recent changes")
        self._process_documents(get_documents(), processors, [lang,], ask_before_saving)
        print("Fix recent changes finished")

    def get_new_contributors(self, contrib_threshold=20, outings_threshold=15):
        with open("contributors.txt", "r") as f:
            contributors = [
                map(int, line.replace("\n", "").split("|")) for line in f.readlines()
            ]

        still_members = {
            d["username"] for d in self.forum.get_group_members("Contributeurs")
        }
        association = {
            d["username"] for d in self.forum.get_group_members("Association")
        }

        excluded = (
            940299,  # rabot
            2,  # camptocamp.association
            1001061,  # botop
            1006785,  # cabot
            108544,  # Modération Topoguide
            154418,  # Moderazione IT
            943665,  # robot.topoguide
            811780,  # compteferme
            108727,  # moderation article
            841148,  # tvmoutain
            383098,  # gite_ecologique_sigoyer_c
            437422,  # Aventures verticales des gorges du Todgha
            # banned
            183887,
            129043,
            812098,
            238764,
            # :'(
            463,
            233,
            282,
            289,
            7274,
            7321,
            2651,
            8602,
            2871,
            5483,
            9063,
            9938,
            1083,
            5926,
            9921,
            8454,
            8719,
            8861,
            8737,
            7956,
            7588,
            9657,
            1959,
            6218,
            3093,
            5951,
            9444,
            2950,
            8844,
            6070,
            7269,
            1158,
            13404,
            11673,
            10490,
            10103,
            12667,
            10888,
            11108,
            12003,
            10133,
            13563,
            483128,
            447865,
            725295,
            492299,
            376440,
            433042,
            359048,
            359048,
            106910,
            372413,
            240992,
            278481,
            522816,
            162444,
            216336,
            270681,
            450463,
            119728,
            235213,
            119310,
            169200,
            106832,
            135490,
            167815,
            130633,
            634898,
            286748,
            109426,
            11879,
            10057,  #
        )

        def display(reason, user, contribs, outings="?"):
            pattern = (
                "<tr>"
                "<td><strong>{reason}</strong></td>"
                "<td>@{forum}</td>"
                '<td><a href="https://www.camptocamp.org/profiles/{user_id}">{name}</a></td>'
                '<td><a href="https://www.camptocamp.org/whatsnew#u={user_id}">{contribs}</a></td>'
                '<td><a href="https://www.camptocamp.org/outings#u={user_id}">{outings}</a></td>'
                "</tr>"
            )

            line = pattern.format(
                reason=reason,
                name=user.name,
                page=user.get_url(),
                forum=user.forum_username,
                contribs=contribs,
                outings=outings,
                user_id=user.document_id,
            )

            print(line)

        print(
            "<table><tr><th>R</th><th>Forum</th><th>Wiki</th><th>Contribs</th><th>Outings</th></tr>"
        )

        for user_id, contribs in contributors:
            if user_id not in excluded:
                try:
                    user = self.wiki.get_profile(user_id)
                except Exception:
                    user = None

                if user:
                    categories = user.categories or []

                    if user.forum_username in still_members:
                        pass

                    elif "institution" in categories or "club" in categories:
                        pass

                    elif user.forum_username in association:
                        display("A", user, contribs)
                        still_members.add(user.forum_username)

                    elif contribs >= contrib_threshold:
                        display("C", user, contribs)
                        still_members.add(user.forum_username)

                    else:

                        outings = self.wiki.get("/outings?u={}".format(user_id))
                        if outings["total"] >= outings_threshold:
                            display("O", user, contribs, outings["total"])
                            still_members.add(user.forum_username)

        for forum_username in association:
            if forum_username not in still_members:
                user = self.wiki.get_user(forum_name=forum_username)
                if user.document_id not in excluded:
                    display("A", user, 0)

        print("</table>")

    def get_users_from_route(self, route_id):
        """
        Get list of user that have done a given route.

        :param route_id: route numrical identifier
        """

        result = {}
        for outing in self.wiki.get_outings({"r": route_id}):
            for user in outing.associations["users"]:
                result[user["document_id"]] = user

        return list(result.values())

    def find_closest_documents(
        self, constructor, longitude, latitude, buffer, filters=None
    ):
        fake_object = {
            "geometry": {
                "geom": "{"
                + '"type":"Point", "coordinates": [{}, {}]'.format(longitude, latitude)
                + "}"
            }
        }

        filters = filters or {}
        filters["bbox"] = ",".join(
            map(
                str,
                [
                    longitude - buffer,
                    latitude - buffer,
                    longitude + buffer,
                    latitude + buffer,
                ],
            )
        )

        result = []

        for document in self.wiki.get_documents(
            constructor=constructor, filters=filters
        ):
            result.append(
                {
                    "document": document,
                    "distance": utils.compute_distance(fake_object, document),
                }
            )

        result.sort(key=lambda item: item["distance"])

        return result


def _parse_filter(url):
    url = url.replace("https://www.camptocamp.org/", "")

    if "#" in url or "?" in url:
        document_type, filters = url.split("?" if "?" in url else "#", 1)
        if len(filters) != 0:
            filters = {k: v for k, v in (v.split("=") for v in filters.split("&"))}
        else:
            filters = {}
    else:
        document_type, filters = url, {}

    for key in filters:
        if key in ("bbox", "date"):
            filters[key] = filters[key].replace("%252C", "%2C")
        elif key in ("act", "rock_type"):
            filters[key] = filters[key].replace("%252C", ",")

    constructor = {
        "profiles": objects.WikiUser,
        "areas": objects.Area,
        "waypoints": objects.Waypoint,
        "outings": objects.Outing,
        "images": objects.Image,
        "maps": objects.Map,
        "xreports": objects.Xreport,
        "articles": objects.Article,
        "books": objects.Book,
        "routes": objects.Route,
    }[document_type]

    return constructor, filters
