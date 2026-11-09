from types import SimpleNamespace

from campbot.checkers import convert_legacy_markup, get_re_tests


def test_convert_legacy_markup():
    assert (
        convert_legacy_markup('<font color="green"><strong>L#</strong></font>')
        == "[color=green]**L#**[/color]"
    )
    assert (
        convert_legacy_markup('<font color="red"><strong>X</strong></font>')
        == "[color=red]**X**[/color]"
    )


def test_other_markers_are_left_alone():
    img = '<img src="/a.png" class="emoji" alt="a">'
    assert convert_legacy_markup(img) == img
    assert convert_legacy_markup(":red_circle:") == ":red_circle:"


def test_configuration_markers_are_converted():
    config = SimpleNamespace(
        raw=(
            "# Test L#\n"
            '* Erreur : <font color="red"><strong>L#</strong></font>\n'
            '* Corrigé : <font color="green"><strong>L#</strong></font>\n'
            "    L#\n"
        )
    )
    (test,) = get_re_tests(config, "fr")
    assert test.fail_marker == "[color=red]**L#**[/color]"
    assert test.success_marker == "[color=green]**L#**[/color]"
