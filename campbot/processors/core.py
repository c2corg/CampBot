import difflib
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
    _tests = None
    langs = None

    def __init__(self):
        self.init_modifiers()
        self.do_tests()

    def init_modifiers(self):
        raise NotImplementedError()

    def do_tests(self):
        def do_test(source, expected):
            result = self.modify(source)
            if result != expected:
                print("Source   ", repr(source))
                print("Expected ", repr(expected))
                print("Result   ", repr(result))
                raise Exception("TEST FAILED")

        for test in self._tests:
            do_test(**test)

    def __call__(self, wiki_object):
        updated = False
        for locale in wiki_object.get("locales", []):
            if self.langs is None or locale.lang in self.langs:
                for field in locale.get_locale_fields():
                    if field in locale and locale[field] and field != "title":
                        markdown = locale[field]
                        new_value = self.modify(markdown)
                        self.print_diff(markdown, new_value)
                        updated = updated or (new_value != markdown)
                        locale[field] = new_value

        return updated

    def print_diff(self, markdown, result):

        if self.ready_for_production:
            d = difflib.Differ()
            diff = d.compare(markdown.replace("\r", "").split("\n"),
                             result.replace("\r", "").split("\n"))
            for dd in diff:
                if dd[0] != " ":
                    print(dd)

    def modify(self, markdown):
        result = markdown

        for modifier in self.modifiers:
            result = modifier(result)

        return result
