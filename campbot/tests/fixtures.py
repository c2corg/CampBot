import json
import io
import pytest
import os


def get_message(filename):
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/" + filename + ".json")
    return json.load(io.open(filename, encoding="utf8"))


messages = [
    # auth
    ("GET", r"https://forum.camptocamp.org/session/csrf", {"csrf": "csrf"}),
    ("POST", r"https://api.camptocamp.org/users/login", {"token": "", "redirect_internal": "/sso", "roles": []}),
    ('GET', r'https://forum.camptocamp.org/sso', {}),

    # specific responses
    ('GET', r'https://api.camptocamp.org/(outings|routes|articles|waypoints)\?.*offset=30.*', {"documents": []}),
    ('GET', r'https://api.camptocamp.org/routes/123/fr/(123|122)', get_message("redirection")),
    ('GET', r'https://api.camptocamp.org/articles/996571', get_message("conf_replacements")),
    ('GET', r'https://api.camptocamp.org/routes/293549/fr/(1738922|1738528)', get_message("route_version")),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/(880880|978249|478470)', get_message("route_version2")),

    # documents
    ('GET', r'https://api.camptocamp.org/outings/\d+', get_message("outing")),
    ('GET', r'https://api.camptocamp.org/profiles/\d+', get_message("user")),
    ('GET', r'https://api.camptocamp.org/routes/\d+', get_message("route")),
    ('GET', r'https://api.camptocamp.org/waypoints/\d+', get_message("waypoint")),
    ('GET', r'https://api.camptocamp.org/images/\d+', get_message("image")),
    ('GET', r'https://api.camptocamp.org/areas/\d+', {}),
    ('GET', r'https://api.camptocamp.org/books/\d+', {}),
    ('GET', r'https://api.camptocamp.org/xreports/\d+', {}),
    ('GET', r'https://api.camptocamp.org/maps/\d+', {}),

    # document list
    ('GET', r'https://api.camptocamp.org/outings(\?.*)?', get_message("outings")),
    ('GET', r'https://api.camptocamp.org/routes(\?.*)?', get_message("routes")),
    ('GET', r'https://api.camptocamp.org/xreports(\?.*)?', get_message("routes")),
    ('GET', r'https://api.camptocamp.org/waypoints(\?.*)?', get_message("routes")),

    # recent changes
    ("GET", r"https://api.camptocamp.org/documents/changes\?limit=50&token=1687339", {"feed": []}),
    ("GET", r"https://api.camptocamp.org/documents/changes.*", get_message("changes")),

    # forum
    ('GET', r'https://forum.camptocamp.org/t/\d+.json\?username_filters=rabot', {"last_posted_at": "2020/01/01"}),
    ('GET', r'https://forum.camptocamp.org/t/\d+.json', get_message("topic")),
    ('GET', r'https://forum.camptocamp.org/posts/\d+.json', get_message("post")),
    ('GET', r'https://forum.camptocamp.org/groups/\w+/members.json.*', get_message("groups")),

    # Misc
    ('GET', r'https://api.camptocamp.org/search.*', get_message("search_user")),
    ('POST', 'https://forum.camptocamp.org/posts', {}),
    ('PUT', '.*', {}),

    ('GET', r'https://forum.camptocamp.org/polls/voters.json.*&offset=0',
     {"poll": {"option_id": [{"username": "CharlesB"}, {"username": "grimpeur8b"}]}}),
    ('GET', r'https://forum.camptocamp.org/polls/voters.json.*&offset=1',
     {"poll": {}}),
]


@pytest.yield_fixture()
def fix_dump():
    from campbot import dump

    _default_db_name = dump._default_db_name
    dump._default_db_name = "test.db"

    yield

    dump._default_db_name = _default_db_name


@pytest.fixture()
def fix_requests():
    from requests import Session
    from campbot import core
    import datetime
    import re

    core.today = lambda: datetime.datetime(year=2017, month=12, day=21)

    class Response(object):
        def __init__(self, method, url, **kwargs):
            self.status = 200
            self.headers = {'Content-type': 'application/json'}

            self._data = None
            for m, pattern, data in messages:
                if m == method and re.fullmatch(pattern, url):
                    self._data = data
                    break

            assert self._data is not None, "Cant find message for {} {}".format(method, url)

            print(method, url, self._data)

        def raise_for_status(self):
            if self.status != 200:
                raise Exception("")

        def json(self):
            return self._data

    def request(self, method, url, **kwargs):
        return Response(method, url, **kwargs)

    core.BaseBot.min_delay = datetime.timedelta(seconds=0.001)

    Session.request = request
