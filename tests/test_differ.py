from tests.fixtures import fix_requests, fix_dump
import pytest

def test_differ():
    from campbot.differ import get_diff_report

    get_diff_report(
        {"1": 1},
        {}
    )

    get_diff_report(
        {},
        {"1": 1}
    )

    get_diff_report(
        {"1": 2},
        {"1": 1}
    )

    with pytest.raises(Exception):
        get_diff_report(set(),tuple())
