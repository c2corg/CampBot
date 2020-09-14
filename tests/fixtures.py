import json
import io
import pytest
import os


def get_message(filename, overwrite_properties=None):
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/" + filename + ".json")
    data = json.load(io.open(filename, encoding="utf-8"))

    if overwrite_properties:
        data.update(overwrite_properties)

    return data


def _wiki(method, url, answer):
    return method, r"https://api.camptocamp.org/" + url, answer,


def _forum(method, url, answer):
    return method, r"https://forum.camptocamp.org/" + url, answer,


messages = [
    # auth
    _forum("GET", r"session/csrf", {"csrf": "csrf"}),
    _forum('GET', r'sso', ""),
    _wiki("POST", r"users/login", {"token": "", "redirect_internal": "/sso", "roles": []}),

    # specific responses
    _wiki('GET', r'(outings|routes|articles|waypoints|xreports)\?.*offset=30.*', {"documents": []}),
    _wiki('GET', r'routes/123/fr/(123|122)', get_message("redirection")),
    _wiki('GET', r'articles/996571', get_message("conf_replacements")),
    _wiki('GET', r'waypoints/\d+/../\d+', get_message("waypoint_version")),
    _wiki('GET', r'routes/293549/fr/(1738922|1738528)', get_message("route_version")),
    _wiki('GET', r'routes/293549/fr/(880880|978249|478470|1738923)', get_message("route_version2")),
    _wiki('GET', r'routes/952126', get_message("route", {'protected': True, 'document_id': 952126})),
    _wiki('GET', r'routes/952167', {'redirects_to': 952126}),
    _wiki('GET', r'profiles/3199', {'document_id': 3199}),
    _wiki('GET', r'documents/changes\?.*&u=3199.*', {'feed': []}),
    _wiki('GET', r'profiles/666', Exception()),

    _wiki('GET', r'profiles/667', {'document_id': 666,
                                   'forum_username': "new_user",
                                   "name": "new_user",
                                   "categories": []}),

    _wiki('GET', r'profiles/668', {'document_id': 666,
                                   'forum_username': "new_user",
                                   "name": "new_user",
                                   "categories": ['club']}),

    # documents
    _wiki('GET', r'outings/\d+', get_message("outing")),
    _wiki('GET', r'profiles/\d+', get_message("user")),
    _wiki('GET', r'routes/\d+', get_message("route")),
    _wiki('GET', r'waypoints/\d+', get_message("waypoint")),
    _wiki('GET', r'images/\d+', get_message("image")),
    _wiki('GET', r'articles/\d+', get_message("article")),
    _wiki('GET', r'areas/\d+', get_message("area")),
    _wiki('GET', r'books/\d+', {}),
    _wiki('GET', r'xreports/\d+', {}),
    _wiki('GET', r'maps/\d+', {}),

    # document list
    _wiki('GET', r'outings(\?.*)?', get_message("outings")),
    _wiki('GET', r'routes(\?.*)?', get_message("routes")),
    _wiki('GET', r'xreports(\?.*)?', get_message("xreports")),
    _wiki('GET', r'waypoints(\?.*)?', get_message("routes")),

    # recent changes
    _wiki("GET", r"documents/changes\?limit=50&token=1687339", {"feed": []}),
    _wiki("GET", r"documents/changes.*", get_message("changes")),

    # forum
    _forum('GET', r't/\d+.json\?username_filters=rabot', {"last_posted_at": "2017-12-21"}),
    _forum('GET', r't/\d+.json', get_message("topic")),
    _forum('GET', r'posts/\d+.json', get_message("post")),
    _forum('GET', r'groups/\w+/members.json.*', get_message("groups")),
    _forum('GET', r'groups/Association.json', get_message("groups_Association")),

    # Misc
    _wiki('GET', r'search.*', get_message("search_user")),
    _forum('POST', r'posts', {}),
    _forum('GET', r'polls/voters.json.*&page=1', {"voters": {"option_id": [{"username": "CharlesB"},
                                                                           {"username": "grimpeur8b"},
                                                                           {"username": "charlesdet"}]}}),
    _forum('GET', r'polls/voters.json.*&page=2', {"voters": {"option_id": []}}),

    ('PUT', '.*', {}),
]


@pytest.yield_fixture()
def fix_dump():
    from campbot import dump

    _default_db_name = dump._default_db_name
    dump._default_db_name = "test.db"

    yield

    dump._default_db_name = _default_db_name


@pytest.yield_fixture()
def fix_requests():
    from requests import Session
    from campbot import core, utils
    import datetime
    import re

    try:
        fullmatch = re.fullmatch
    except AttributeError:  # py 2.7
        def fullmatch(regex, string, flags=0):
            """Emulate python-3.4 re.fullmatch()."""
            return re.match("(?:" + regex + r")\Z", string, flags=flags)

    class Response(object):
        def __init__(self, method, url, **kwargs):
            self.status = 200
            self.headers = {}

            self._data = None
            for m, pattern, data in messages:
                if m == method and fullmatch(pattern, url):
                    self._data = data
                    break

            self.headers['Content-type'] = 'application/json' if isinstance(self._data, dict) else ''
            assert self._data is not None, "Cant find message for {} {}".format(method, url)

            print(method, url, self._data)

            if isinstance(self._data, Exception):
                self.status = 500

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

        @property
        def content(self):
            return self._data

    def request(self, method, url, **kwargs):
        return Response(method, url, **kwargs)

    today = utils.today

    utils.today = lambda: datetime.datetime(year=2017, month=12, day=21)
    core.BaseBot.min_delay = datetime.timedelta(seconds=0.001)
    Session.request = request

    yield

    utils.today = today


@pytest.yield_fixture()
def ids_files():
    filename = "ids.txt"

    with open(filename, "w") as f:
        f.write("123|r\n")
        f.write("456|w\n")

    yield filename

    os.remove(filename)


@pytest.yield_fixture()
def fix_input():
    from campbot import objects

    class MockInput(object):
        def _callback(self, message):
            return "n"

        def __call__(self, message):
            answer = self._callback(message)
            print(message, answer)
            return answer

        def set_response(self, callback):
            self._callback = callback

    backup = objects._input
    objects._input = MockInput()

    yield objects._input

    objects._input = backup
