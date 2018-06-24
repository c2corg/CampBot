from .bbcode import BBCodeRemover, ColorAndUnderlineRemover, InternalLinkCorrector
from .cleaners import MarkdownCleaner, AutomaticReplacements, SpaceBetweenNumberAndUnit, MultiplicationSign, UpperFix, \
    OrthographicProcessor
from .ltagmigrator import LtagCleaner, LtagMigrator


def get_automatic_replacments(bot, clean_bbcode=False):
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
                    needle, stack = line.split(">>")
                    test["replacements"].append((needle.strip(), stack.strip()))

    result = [AutomaticReplacements(**args) for args in result if len(args["replacements"]) != 0]

    if clean_bbcode:
        result.append(BBCodeRemover())
        result.append(ColorAndUnderlineRemover())
        result.append(InternalLinkCorrector())

    result.append(SpaceBetweenNumberAndUnit())
    result.append(MultiplicationSign())
    result.append(UpperFix())

    return result
