import requests
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import logging
import time


class BaseBot(object):
    api_url = NotImplemented
    min_delay = timedelta(seconds=1)

    def __init__(self):
        self.proxies = None
        self._next_request_datetime = datetime.now()
        self.headers = {}

    def _wait(self):
        to_wait = (self._next_request_datetime - datetime.now()).total_seconds()

        if to_wait > 0:
            time.sleep(to_wait)

        self._next_request_datetime = datetime.now() + self.min_delay

    def _get(self, url):
        self._wait()
        logging.debug("GET %s", url)
        return requests.get(self.api_url + url,
                            headers=self.headers,
                            proxies=self.proxies).json()

    def _post(self, url, data):
        self._wait()
        logging.debug("POST %s", url)
        return requests.post(self.api_url + url, json=data,
                             headers=self.headers,
                             proxies=self.proxies).json()


class CampBot(BaseBot):
    api_url = "https://api.camptocamp.org"

    def login(self, credentials):
        token = self._post("/users/login", credentials)["token"]
        self.headers["Authorization"] = 'JWT token="{}"'.format(token)

    def get_editions(self, **kwargs):

        oldest_date = kwargs.get("oldest_date", datetime.today() + timedelta(days=-180))
        oldest_date = oldest_date.replace(tzinfo=pytz.UTC)

        d = self._get("/documents/changes?limit=50")
        while True:
            for item in d["feed"]:
                if oldest_date > parser.parse(item["written_at"]):
                    raise StopIteration

                yield item

            pagination_token = d["pagination_token"]
            d = self._get("/documents/changes?limit=50&token=" + pagination_token)

    def list_contributors(self, **kwargs):
        contributors = {}

        for item in self.get_editions(**kwargs):
            contributors[item["user"]["user_id"]] = item["user"]

        return contributors.values()

    def get_profile(self, user_id):
        return self._get("/profiles/{}".format(user_id))


class ForumBot(BaseBot):
    api_url = "https://forum.camptocamp.org"

    def get_voters(self, post_id):
        return self._get("/polls/voters.json?post_id={}&poll_name=poll".format(post_id))
