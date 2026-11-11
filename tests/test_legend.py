from types import SimpleNamespace

from campbot.checkers import build_legend


def _test(name, fail, success):
    return SimpleNamespace(name=name, fail_marker=fail, success_marker=success)


def test_legend_is_a_markdown_table_without_html():
    legend = build_legend(
        [
            _test("Termes suspects", "[color=red]**?**[/color]", "."),
            _test(
                "Diverses erreurs",
                "[color=red]**X**[/color]",
                "[color=green]**X**[/color]",
            ),
        ]
    )

    # BBCode is not interpreted inside HTML blocks, so no HTML table
    assert "<table>" not in legend and "<td>" not in legend
    assert legend.startswith("[details=Signification des icônes]\n\n| Test |")
    assert "|---|---|---|" in legend
    assert "| Termes suspects | [color=red]**?**[/color] | . |" in legend
    assert legend.endswith("[/details]")


def test_legend_cells_cannot_break_the_table():
    legend = build_legend([_test("a|b", "", "x\ny")])
    assert "| a&#124;b |   | x y |" in legend
