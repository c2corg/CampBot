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


class ForumBot(BaseBot):
    def get_voters(self, post_id, poll_name=None):
        poll_name = poll_name or "poll"
        return self.get("/polls/voters.json?post_id={}&poll_name={}".format(post_id, poll_name))[poll_name]

    def get_group_members(self, group_name):
        return self.get("/groups/{}/members.json".format(group_name))


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

    def check_voters(self, post_id, poll_name=None):
        voters = []
        data = self.forum.get_voters(post_id, poll_name)
        for item in data:
            voters += data[item]

        contributors = {u["forum_username"]: u for u in self.get_contributors()}

        print("forum", "status")
        for voter in voters:
            print(voter["username"], voter["username"] in contributors)
