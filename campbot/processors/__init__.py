from .bbcode import BBCodeRemover, ColorAndUnderlineRemover, InternalLinkCorrector
from .cleaners import (
    MarkdownCleaner,
    AutomaticReplacements,
    DiacriticsFix,
    SpaceBetweenNumberAndUnit,
    MultiplicationSign,
    UpperFix,
    OrthographicProcessor,
    RemoveColonInHeader,
    FixFakeExternalLinks,
)
from .ltagmigrator import LtagCleaner, LtagMigrator


def get_automatic_replacments(bot, clean_bbcode=False, replacements_version=None):
    if replacements_version is None:
        article = bot.wiki.get_article(996571)
    else:
        article = bot.wiki.get_wiki_object_version(
            996571, "c", "fr", replacements_version
        )

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

    processors = [
        DiacriticsFix(),
    ]
    processors += [
        AutomaticReplacements(**args)
        for args in result
        if len(args["replacements"]) != 0
    ]

    if clean_bbcode:
        processors.append(BBCodeRemover())
        processors.append(ColorAndUnderlineRemover())
        processors.append(InternalLinkCorrector())

    processors.append(SpaceBetweenNumberAndUnit())
    processors.append(MultiplicationSign())
    processors.append(UpperFix())
    processors.append(RemoveColonInHeader())
    processors.append(FixFakeExternalLinks())

    return processors
