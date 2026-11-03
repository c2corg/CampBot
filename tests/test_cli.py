"""Functional tests of the command line: each command is run as a user would."""

import subprocess
import sys

import pytest

from tests.fixtures import fix_requests

THREAD = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480"

COMMANDS = {
    "report_rc": ["report_rc", "1", "fr", THREAD],
    "clean_rc": ["clean_rc", "1", "fr", THREAD, "--batch"],
    "report": ["report", "routes#w=123", "fr"],
    "clean": ["clean", "routes#w=123", "fr", THREAD, "--batch", "--bbcode"],
    "contribs": ["contribs", "--starts=2017-06-01", "--ends=2017-12-31"],
    "export": ["export", "outings#u=286726"],
}


@pytest.fixture()
def credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("CAMPBOT_LOGIN", "x")
    monkeypatch.setenv("CAMPBOT_PASSWORD", "y")
    monkeypatch.setenv("HTTPS_PROXY", "")
    monkeypatch.chdir(tmp_path)  # commands write their CSV in the current directory


@pytest.mark.parametrize("command", COMMANDS)
def test_command_runs(fix_requests, credentials, monkeypatch, command):
    from campbot.__main__ import main_entry_point

    monkeypatch.setattr(
        sys, "argv", ["campbot"] + COMMANDS[command] + ["--delay=0.001"]
    )

    main_entry_point()


@pytest.mark.parametrize("command", COMMANDS)
def test_command_help(monkeypatch, capsys, command):
    from campbot.__main__ import main_entry_point

    monkeypatch.setattr(sys, "argv", ["campbot", command, "-h"])

    with pytest.raises(SystemExit) as exit:
        main_entry_point()

    assert exit.value.code in (0, None)  # None: docopt
    assert command in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv", [[], ["unknown"], ["export"], ["clean", "routes#w=123", "fr"]]
)
def test_invalid_command_line_is_refused(monkeypatch, capsys, argv):
    from campbot.__main__ import main_entry_point

    monkeypatch.setattr(sys, "argv", ["campbot"] + argv)

    with pytest.raises(SystemExit) as exit:
        main_entry_point()

    assert exit.value.code != 0


def test_module_can_be_run():
    result = subprocess.run(
        [sys.executable, "-m", "campbot", "-h"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "clean_rc" in result.stdout


def test_report_over_several_days(fix_requests, credentials, monkeypatch):
    from campbot.__main__ import main_entry_point

    argv = ["campbot", "report_rc", "3", "fr", THREAD, "--delay=0.001"]
    monkeypatch.setattr(sys, "argv", argv)

    main_entry_point()
