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
    ('GET', r'https://forum.camptocamp.org/sso', ""),

    # specific responses
    ('GET', r'https://api.camptocamp.org/(outings|routes|articles|waypoints)\?.*offset=30.*', {"documents": []}),
    ('GET', r'https://api.camptocamp.org/routes/123/fr/(123|122)', get_message("redirection")),
    ('GET', r'https://api.camptocamp.org/articles/996571', get_message("conf_replacements")),
    ('GET', r'https://api.camptocamp.org/routes/293549/fr/(1738922|1738528)', get_message("route_version")),
    ('GET', 'https://api.camptocamp.org/routes/293549/fr/(880880|978249|478470|1738923)', get_message("route_version2")),
    ('GET', 'https://api.camptocamp.org/routes/952126', {'protected': True, 'document_id': 952126}),
    ('GET', 'https://api.camptocamp.org/routes/952167', {'redirects_to': 952126}),
    ('GET', r'https://api.camptocamp.org/profiles/3199', {'document_id': 3199}),
    ('GET', r'https://api.camptocamp.org/documents/changes\?.*&u=3199.*', {'feed': []}),
    ('GET', r'https://api.camptocamp.org/profiles/666', Exception()),
    ('GET', r'https://api.camptocamp.org/profiles/667',
     {'document_id': 666, 'forum_username': "new_user", "name": "new_user", "categories": []}),
    ('GET', r'https://api.camptocamp.org/profiles/668',
     {'document_id': 666, 'forum_username': "new_user", "name": "new_user", "categories": ['club']}),

    # documents
    ('GET', r'https://api.camptocamp.org/outings/\d+', get_message("outing")),
    ('GET', r'https://api.camptocamp.org/profiles/\d+', get_message("user")),
    ('GET', r'https://api.camptocamp.org/routes/\d+', get_message("route")),
    ('GET', r'https://api.camptocamp.org/waypoints/\d+', get_message("waypoint")),
    ('GET', r'https://api.camptocamp.org/images/\d+', get_message("image")),
    ('GET', r'https://api.camptocamp.org/articles/\d+', get_message("article")),
    ('GET', r'https://api.camptocamp.org/areas/\d+', get_message("area")),
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
    ('GET', r'https://forum.camptocamp.org/t/\d+.json\?username_filters=rabot', {"last_posted_at": "2017-12-21"}),
    ('GET', r'https://forum.camptocamp.org/t/\d+.json', get_message("topic")),
    ('GET', r'https://forum.camptocamp.org/posts/\d+.json', get_message("post")),
    ('GET', r'https://forum.camptocamp.org/groups/\w+/members.json.*', get_message("groups")),
    ('GET', r'https://forum.camptocamp.org/groups/Association.json', get_message("groups_Association")),

    # Misc
    ('GET', r'https://api.camptocamp.org/search.*', get_message("search_user")),
    ('POST', 'https://forum.camptocamp.org/posts', {}),
    ('PUT', '.*', {}),

    ('GET', r'https://forum.camptocamp.org/polls/voters.json.*&offset=0',
     {"poll": {"option_id": [{"username": "CharlesB"}, {"username": "grimpeur8b"}, {"username": "charlesdet"}]}}),

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
        def __call__(self, message):
            return ""

        def set_response(self, callback):
            self.__call__ = callback

    backup = objects._input
    objects._input = MockInput()

    yield objects._input

    objects._input = backup
