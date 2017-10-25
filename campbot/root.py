from __future__ import print_function, unicode_literals, division

import requests
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import logging
import time


class BaseBot(object):
    min_delay = timedelta(seconds=1)

    def __init__(self, api_url, proxies=None):
        self.api_url = api_url
        self._session = requests.Session()
        self.proxies = proxies
        self._next_request_datetime = datetime.now()

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
    def get_editions(self, **kwargs):

        oldest_date = kwargs.get("oldest_date", datetime.today() + timedelta(days=-1))
        oldest_date = oldest_date.replace(tzinfo=pytz.UTC)

        d = self.get("/documents/changes?limit=50")
        while True:
            for item in d["feed"]:
                if oldest_date > parser.parse(item["written_at"]):
                    raise StopIteration

                yield item

            pagination_token = d["pagination_token"]
            d = self.get("/documents/changes?limit=50&token=" + pagination_token)

    def get_profile(self, user_id):
        return self.get("/profiles/{}".format(user_id))

    def edit_profile(self, user_id, edit_foo):
        doc = self.get_profile(user_id)
        doc, message = edit_foo(doc)
        payload = {"document": doc, "message": message}
        return self.put("/profiles/{}".format(user_id), payload)


class ForumBot(BaseBot):
    def get_voters(self, topic_id=None, post_number=None, url=None):
        post = self.get_post(topic_id=topic_id, post_number=post_number, url=url)

        result = {}
        for poll_name in post["polls"]:
            result[poll_name] = self.get("/polls/voters.json?post_id={}&poll_name={}".format(post["id"], poll_name))[
                poll_name]

        return result

    def get_group_members(self, group_name):
        result = []

        expected_len = 1
        while len(result) < expected_len:
            data = self.get("/groups/{}/members.json?limit=50&offset={}".format(group_name, len(result)))
            expected_len = data["meta"]["total"]
            result += data["members"]

        return result

    def get_topic(self, topic_id):
        return self.get("/t/{}.json".format(topic_id))

    def get_post(self, topic_id=None, post_number=None, url=None):
        if url:
            url = url.replace(self.api_url, "").split("/")
            assert url[1] == 't'
            topic_id = url[3]
            post_number = int(url[4].split("?")[0])

        topic = self.get_topic(topic_id)
        post_id = topic["post_stream"]["stream"][post_number - 1]

        return self.get("/posts/{}.json".format(post_id))


class CampBot(object):
    def __init__(self, proxies=None):
        self.wiki = WikiBot("https://api.camptocamp.org", proxies=proxies)
        self.forum = ForumBot("https://forum.camptocamp.org", proxies=proxies)

        self.forum.headers['X-Requested-With'] = "XMLHttpRequest"
        self.forum.headers['Host'] = "forum.camptocamp.org"

    def login(self, login, password):
        res = self.wiki.post("/users/login", {"username": login, "password": password, "discourse": True})
        token = res["token"]
        self.wiki.headers["Authorization"] = 'JWT token="{}"'.format(token)
        self.forum.get(res["redirect_internal"].replace(self.forum.api_url, ""))

    def get_contributors(self, **kwargs):

        contributors = {}

        for item in self.wiki.get_editions(**kwargs):
            contributors[item["user"]["user_id"]] = item["user"]

        result = []
        for user in contributors.values():
            result.append(self.wiki.get_profile(user["user_id"]))

        return result

    def check_voters(self, url, allowed_groups=()):

        allowed_members = []
        for group in allowed_groups:
            allowed_members += self.forum.get_group_members(group)

        allowed_members = {u["username"]: u for u in allowed_members}
        contributors = {u["forum_username"]: u for u in self.get_contributors()}

        polls = self.forum.get_voters(url=url)
        for poll_name in polls:
            voters = []
            for item in polls[poll_name]:
                voters += polls[poll_name][item]

            print(poll_name, ",", len(voters), "voters : ")
            for voter in voters:
                if voter["username"] not in contributors and voter["username"] not in allowed_members:
                    print("    ", voter["username"], "is not allowed")

            print()

    def get_user(self, wiki_name=None, forum_name=None):
        name = wiki_name or forum_name

        data = self.wiki.get("/search?q={}&t=u&limit=50".format(name))

        prop = "name" if wiki_name else "forum_username"

        for item in data["users"]["documents"]:
            if item[prop] == name:
                return item

        return None