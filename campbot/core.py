from __future__ import print_function, unicode_literals, division

import requests
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import logging
import time

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

        res = self._session.post(self.api_url + url, json=data,
                                 proxies=self.proxies)

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
    def get_wiki_object(self, constructor, id):
        return constructor(self.campbot, self.get("/{}/{}".format(constructor.url_path, id)))

    def get_route(self, route_id):
        return self.get_wiki_object(objects.Route, route_id)

    def get_waypoint(self, waypoint_id):
        return self.get_wiki_object(objects.Waypoint, waypoint_id)

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
    def get_group_members(self, group_name):
        result = []

        expected_len = 1
        while len(result) < expected_len:
            data = self.get("/groups/{}/members.json?limit=50&offset={}".format(group_name, len(result)))
            expected_len = data["meta"]["total"]
            result += data["members"]

        return [objects.ForumUser(self.campbot, user) for user in result]

    def get_topic(self, topic_id=None, url=None):
        if url:
            url = url.replace(self.api_url, "").split("?")[0].split("/")
            assert url[1] == 't'
            topic_id = int(url[3])

        return self.get("/t/{}.json".format(topic_id))

    def get_post(self, topic_id=None, post_number=None, url=None):
        if url:
            url = url.replace(self.api_url, "").split("?")[0].split("/")
            assert url[1] == 't'
            topic_id = url[3]
            post_number = int(url[4]) if len(url) >= 5 else 1

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

        self.forum.headers['X-Requested-With'] = "XMLHttpRequest"
        self.forum.headers['Host'] = "forum.camptocamp.org"

    def login(self, login, password):
        res = self.wiki.post("/users/login", {"username": login, "password": password, "discourse": True})
        token = res["token"]
        self.wiki.headers["Authorization"] = 'JWT token="{}"'.format(token)
        self.forum.get(res["redirect_internal"].replace(self.forum.api_url, ""))

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
                     route_ids=None, waypoint_ids=None, area_ids=None, user_ids=None):

        logging.info("Fix markdown with {} processor".format(processor  ))
        logging.info("Ask before saving : {}".format(ask_before_saving))
        logging.info("Delay between each request : {}".format(self.wiki.min_delay))

        for ids, constructor in [(route_ids, objects.Route),
                                 (waypoint_ids, objects.Waypoint),
                                 (area_ids, objects.Area), ]:
            for id in (ids or []):
                item = self.wiki.get_wiki_object(constructor, id)
                url = "https://www.camptocamp.org/{}/{}".format(constructor.url_path, id)

                if "redirects_to" in item:
                    print("{} is a redirection".format(url))

                elif item.protected:
                    print("{} is protected".format(url))

                elif not item.is_valid():
                    print("{} : {}".format(url, item.get_invalidity_reason()))

                elif item.fix_markdown(processor):
                    if not processor.ready_for_production:
                        print("{} is impacted".format(url))

                    elif not ask_before_saving or input("Save {} y/[n]?".format(url)) == "y":
                        print("Saving {}".format(url))
                        item.save(processor.comment)

                    print()
                else:
                    print("Nothing found on {}".format(url))
