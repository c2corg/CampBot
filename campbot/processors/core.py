import re


class Converter(object):
    def __init__(self, pattern, repl, flags=0):
        self.re = re.compile(pattern=pattern, flags=flags)
        self.repl = repl
        self.flags = flags

    def __call__(self, text):
        return self.re.sub(repl=self.repl, string=text)


class MarkdownProcessor(object):
    modifiers = []
    ready_for_production = False
    comment = NotImplemented
    lang = None

    def __init__(self):
        self.init_modifiers()

    def init_modifiers(self):
        raise NotImplementedError()

    def __call__(self, wiki_object, langs):
        updated = False
        for locale in wiki_object.get("locales", []):
            if self.lang is None or locale.lang == self.lang:
                if langs is None or locale.lang in langs:
                    for field in locale.get_locale_fields():
                        if (
                            field in locale
                            and locale[field]
                            and field not in ("title", "slope", "external_resources")
                        ):
                            markdown = locale[field]
                            new_value = self.modify(markdown)
                            updated = updated or (new_value != markdown)
                            locale[field] = new_value

        return updated

    def modify(self, markdown):
        result = markdown

        for modifier in self.modifiers:
            result = modifier(result)

        return result
