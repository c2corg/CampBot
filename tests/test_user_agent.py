import requests
import pytest

from campbot import CampBot, __version__
from campbot.core import build_user_agent

CAMPBOT_UA = "CampBot/{} (+https://github.com/c2corg/CampBot)".format(__version__)


def _sent_user_agent(bot):
    request = requests.Request("GET", bot.api_url + "/routes")
    return bot._session.prepare_request(request).headers["User-Agent"]


def test_campbot_names_itself_by_default():
    bot = CampBot()

    assert _sent_user_agent(bot.wiki) == CAMPBOT_UA
    assert _sent_user_agent(bot.forum) == CAMPBOT_UA


def test_tool_built_on_campbot_comes_first():
    bot = CampBot(user_agent="MyTool/1.2 (+https://example.org/mytool)")

    expected = "MyTool/1.2 (+https://example.org/mytool) " + CAMPBOT_UA
    assert _sent_user_agent(bot.wiki) == expected
    assert _sent_user_agent(bot.forum) == expected


@pytest.mark.parametrize("user_agent", [None, "", "  "])
def test_empty_tool_name_is_ignored(user_agent):
    assert build_user_agent(user_agent) == CAMPBOT_UA


def test_command_line_option(monkeypatch):
    from campbot.__main__ import build_parser, get_campbot

    for name in ("CAMPBOT_LOGIN", "CAMPBOT_PASSWORD", "CAMPBOT_CREDENTIALS"):
        monkeypatch.delenv(name, raising=False)
    args = build_parser().parse_args(
        ["export", "outings#u=2", "--user-agent=MyTool/1.2"]
    )

    bot = get_campbot(args)

    assert _sent_user_agent(bot.wiki) == "MyTool/1.2 " + CAMPBOT_UA
