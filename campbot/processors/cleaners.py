from .core import MarkdownProcessor, Converter
import re


class MarkdownCleaner(MarkdownProcessor):
    ready_for_production = True
    comment = "Clean markdown"

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

        def protect(pattern, ph, markdown):

            def repl(match):
                markdown = match.group(0)

                if markdown not in placeholders:
                    placeholders[markdown] = ph.format(len(placeholders))

                return placeholders[markdown]

            return re.sub(pattern, repl, markdown)

        result = markdown

        result = protect(r"https?://[^ )\n>]*", "http://{}.markdown___placeholder.com", result)
        result = protect(r"\[\[[a-z]+/\d+/[/a-z\-#]+\|", "[[md___ph/666/{}|", result)
        result = protect(r":\w+:", ":emoji___ph{}:", result)

        result = super().modify(result)

        for url, placeholder in placeholders.items():
            result = result.replace(placeholder, url)

        return result


class UpperFix(OrthographicProcessor):
    comment = "Upper case first letter"
    ready_for_production = True

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

    def init_modifiers(self):
        self.modifiers = [

            Converter(r"(\b\d)([*xX])(\d+) ?(m\b)",
                      r"\1×\3 \4")
        ]


class SpaceBetweenNumberAndUnit(OrthographicProcessor):
    lang = "fr"
    comment = "Espace entre chiffre et unité"
    ready_for_production = True

    def init_modifiers(self):
        self.modifiers = [
            Converter(r"(^|[| \n\(])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2 \3\4"),

            Converter(r"(^|[| \n\(])(\d+)([\-xX])(\d+)(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])",
                      r"\1\2\3\4 \5\6"),
        ]


class AutomaticReplacements(OrthographicProcessor):
    ready_for_production = True

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
