from campbot import CampBot
from campbot.objects import ShortWikiUser


def test_contributions_url_uses_a_query_string():
    # the UI reads filters from the query string: with a #fragment the page
    # shows the unfiltered list until it is refreshed
    user = ShortWikiUser(CampBot(), {"user_id": 1965741, "name": "x"})
    assert (
        user.get_contributions_url() == "https://www.camptocamp.org/whatsnew?u=1965741"
    )
