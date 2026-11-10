from campbot.checkers import emoji
from campbot.core import split_message


def test_short_message_is_not_split():
    assert split_message("coucou\nle monde", 100) == ["coucou\nle monde"]


def test_long_message_is_split_on_lines_and_lossless():
    lines = ["line {} ".format(i) + "x" * 40 for i in range(200)]
    message = "\n".join(lines)
    chunks = split_message(message, 1000)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    assert "\n".join(chunks) == message


def test_overlong_line_is_cut():
    chunks = split_message("a" * 2500, 1000)
    assert [len(c) for c in chunks] == [1000, 1000, 500]


def test_post_message_posts_each_chunk(monkeypatch):
    from campbot import CampBot
    from campbot.core import ForumBot

    bot = CampBot()
    posted = []
    monkeypatch.setattr(ForumBot, "_get_post_ids", lambda self, url: (42, 1))
    monkeypatch.setattr(ForumBot, "post", lambda self, url, data: posted.append(data))
    monkeypatch.setattr(ForumBot, "MAX_POST_LENGTH", 100)
    monkeypatch.setattr("campbot.core.time.sleep", lambda s: None)

    bot.forum.post_message("\n".join(["y" * 40] * 10), "https://x/t/a/42")

    assert len(posted) > 1
    assert all(p["topic_id"] == 42 and len(p["raw"]) <= 100 for p in posted)


def test_emoji_has_explicit_size():
    html = emoji("/images/emoji/apple/red_circle.png?v=3", "t")
    assert 'width="20"' in html and 'height="20"' in html


def test_parts_are_spaced_and_rate_limit_is_retried(monkeypatch):
    from campbot import CampBot
    from campbot.core import ForumBot
    from tests.test_rate_limit import fake_server

    sleeps = []
    monkeypatch.setattr("campbot.core.time.sleep", sleeps.append)
    monkeypatch.setattr(ForumBot, "_get_post_ids", lambda self, url: (42, 1))
    monkeypatch.setattr(ForumBot, "MAX_POST_LENGTH", 100)
    # second request is rate limited once
    calls = fake_server(
        monkeypatch, [200, (429, {"extras": {"wait_seconds": 7}}), 200, 200]
    )

    CampBot(min_delay=0).forum.post_message(
        "\n".join(["y" * 40] * 6), "https://x/t/a/42"
    )

    assert calls[1]["json"] == calls[2]["json"]  # the rate limited part, sent again
    assert len(calls) == 4  # 3 parts, one of them sent twice
    assert 9 in sleeps  # 7s asked by the forum + margin
    assert sleeps.count(ForumBot.POST_INTERVAL) == 2  # between 3 parts
