import pytest

from campbot.checkers import TitleLevelTest, _format_timestamp


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", True),
        ("Just text, no title", True),
        ("## Access\ntext\n### Detail", True),
        ("## Access", True),
        ("# Access\n## Detail", False),
        ("### Access\ntext", False),
        ("### A\n### B", False),
        ("text # not a title\n##Not a title either", True),
        ("text\n\n### Late title", False),
    ],
)
def test_title_level(text, expected):
    class Locale(dict):
        def __getattr__(self, name):
            return self[name]

        def get_locale_fields(self):
            return ("description",)

    class Document:
        def get_locale(self, lang):
            return Locale(description=text) if lang == "fr" else None

    test = TitleLevelTest("fr")

    assert test.test_document(Document()) is expected
    assert TitleLevelTest("de").test_document(Document()) is True


def test_report_timestamp():
    written_at = "2023-09-07T14:05:00.000000+00:00"

    assert _format_timestamp(written_at, with_date=False) == "14:05"
    assert _format_timestamp(written_at, with_date=True) == "07/09 14:05"
