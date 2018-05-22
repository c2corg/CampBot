from .core import MarkdownProcessor, Converter
import re


class MarkdownCleaner(MarkdownProcessor):
    ready_for_production = True
    comment = "Clean markdown"

    _tests = [
        {
            "source": "\n\nx\n\nx\nx\n\n\nx\n\n",
            "expected": "x\n\nx\nx\n\nx",
        },
        {
            "source": "#a\n##  b\n# c",
            "expected": "# a\n## b\n# c",
        }
    ]

    def init_modifiers(self):
        self.modifiers = [
            Converter(pattern=r"\n{3,}",
                      repl=r"\n\n"),

            Converter(pattern=r"^\n*",
                      repl=r""),

            Converter(pattern=r"\n*$",
                      repl=r""),

            Converter(pattern=r"(^|\n)(#+) *",
                      repl=r"\1\2 "),
        ]


class OrthographicProcessor(MarkdownProcessor):
    def modify(self, markdown):
        placeholders = {}

        def _get_placeholder(match):
            url = match.group(0)

            if url not in placeholders:
                placeholders[url] = "http://{}.markdown_placeholder.com".format(len(placeholders))

            return placeholders[url]

        result = re.sub(r"https?://[^ )\n]*", _get_placeholder, markdown)

        result = super().modify(result)

        for url, placeholder in placeholders.items():
            result = result.replace(placeholder, url)

        return result


class UpperFix(OrthographicProcessor):
    comment = "Upper case first letter"
    ready_for_production = True

    _tests = [{
        "source": "## abc\n#ab\n#\n##A",
        "expected": "## Abc\n#Ab\n#\n##A",
    }, {
        "source": "|aa\nL# | aa | Aa [[routes/132|aa]] | \n a \n|a\na\n\naa",
        "expected": "|aa\nL# | Aa | Aa [[routes/132|aa]] | \n a \n|A\na\n\naa",
    }]

    def init_modifiers(self):
        def upper(match):
            return match.group(0).upper()

        def ltag_converter(markdown):
            result = []

            cell_pattern = re.compile(r'(\| *[a-z])(?![^|]*\]\])')

            is_ltag = False

            for line in markdown.split("\n"):

                if len(line) == 0:
                    is_ltag = False

                if line.startswith("L#") or line.startswith("R#"):
                    is_ltag = True

                if is_ltag:
                    result.append(cell_pattern.sub(upper, line))

                else:
                    result.append(line)

            return "\n".join(result)

        self.modifiers = [
            Converter(r"(^|\n)#+ *[a-z]",
                      upper),
            ltag_converter,
        ]


class MultiplicationSign(OrthographicProcessor):
    comment = "Multiplication sign"
    ready_for_production = True

    _tests = [

        {"source": "2*50m, 2x50 m, 2X50 m",
         "expected": "2×50 m, 2×50 m, 2×50 m"},
    ]

    def init_modifiers(self):
        self.modifiers = [

            Converter(r"(\b\d)([*xX])(\d+) ?(m\b)",
                      r"\1×\3 \4")
        ]


class SpaceBetweenNumberAndUnit(OrthographicProcessor):
    lang = "fr"
    comment = "Espace entre chiffre et unité"
    ready_for_production = True

    _tests = [
        {"source": "",
         "expected": ""},
        {"source": "prendre une corde 10-15m ou 2x50m ou 2X50m",
         "expected": "prendre une corde 10-15 m ou 2x50 m ou 2X50 m"},
        {"source": "6h, 2min! 4mn? 5m et 6km",
         "expected": "6 h, 2 min! 4 mn? 5 m et 6 km"},
        {"source": "L# | 30m |",
         "expected": "L# | 30 m |"},
        {"source": "L# |30m |",
         "expected": "L# |30 m |"},
        {"source": "L# | 30m|",
         "expected": "L# | 30 m|"},
        {"source": "6h\n",
         "expected": "6 h\n"},
        {"source": "\n6h\n",
         "expected": "\n6 h\n"},
        {"source": "\n6h",
         "expected": "\n6 h"},
        {"source": "L#6h",
         "expected": "L#6h"},
        {"source": " 6A ",
         "expected": " 6A "},
    ]

    def init_modifiers(self):
        self.modifiers = [
            Converter(r"(^|[| \n\(])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2 \3\4"),

            Converter(r"(^|[| \n\(])(\d+)([\-xX])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2\3\4 \5\6"),
        ]


class AutomaticReplacements(OrthographicProcessor):
    ready_for_production = True
    _tests = []

    def __init__(self, lang, comment, replacements):
        self.replacements = replacements
        super().__init__()
        self.lang = lang
        self.comment = comment
        self.placeholders = None

    def init_modifiers(self):
        self.modifiers = []

        for old, new in self.replacements:
            self.modifiers.append(
                Converter(
                    r"\b" + old.strip() + r"\b",
                    new.strip()
                )
            )


def get_automatic_replacments(bot):
    article = bot.wiki.get_article(996571)
    result = []

    for locale in article.locales:
        lang = locale.lang
        configuration = locale.description
        test = None
        for line in configuration.split("\n"):
            if line.startswith("#"):
                test = {"lang": lang, "comment": line.lstrip("# "), "replacements": []}
                result.append(test)

            elif line.startswith("    ") and test:
                pattern = line[4:]
                if len(pattern.strip()) != 0:
                    test["replacements"].append(line[4:].split(">>"))

    result = [AutomaticReplacements(**args) for args in result if len(args["replacements"]) != 0]

    result.append(SpaceBetweenNumberAndUnit())
    result.append(MultiplicationSign())
    result.append(UpperFix())

    return result
