from __future__ import print_function, unicode_literals, division

import difflib
import re

__all__ = ['MarkdownProcessor', 'BBCodeRemover']


class Converter(object):
    def __init__(self, pattern, repl, flags):
        self.re = re.compile(pattern=pattern, flags=flags)
        self.repl = repl
        self.flags = flags

    def __call__(self, text):
        return self.re.sub(repl=self.repl, string=text)


class MarkdownProcessor(object):
    def __call__(self, markdown, field, locale, wiki_object):
        raise NotImplementedError()


class BBCodeRemover(MarkdownProcessor):
    def __init__(self):
        def get_typo_cleaner(bbcode_tag, markdown_tag):
            converters = [

                Converter(pattern=r'\[' + bbcode_tag + r'\]\[/' + bbcode_tag + '\]',
                          repl=r"",
                          flags=re.IGNORECASE),

                Converter(pattern=r'\n *\[' + bbcode_tag + r'\] *',
                          repl=r"\n[" + bbcode_tag + r"]",
                          flags=re.IGNORECASE),

                Converter(pattern=r'\[' + bbcode_tag + r'\] +',
                          repl=r" [" + bbcode_tag + r"]",
                          flags=re.IGNORECASE),

                Converter(pattern=r' +\[/' + bbcode_tag + r'\]',
                          repl=r"[/" + bbcode_tag + r"] ",
                          flags=re.IGNORECASE),

                Converter(pattern=r'\r\n\[/' + bbcode_tag + r'\]',
                          repl=r"[/" + bbcode_tag + r"]\r\n",
                          flags=re.IGNORECASE),

                Converter(pattern=r'\[' + bbcode_tag + r'\] *\r\n([^\*\#]?)',
                          repl=r"\r\n[" + bbcode_tag + r"]\1",
                          flags=re.IGNORECASE),

                Converter(pattern=r'\[' + bbcode_tag + r'\]([^\n\r\*\`]*?)\[/' + bbcode_tag + '\]',
                          repl=markdown_tag + r"\1" + markdown_tag,
                          flags=re.IGNORECASE),
            ]

            def result(markdown):
                for converter in converters:
                    markdown = converter(markdown)

                return markdown

            return result

        self.cleaners = [
            get_typo_cleaner("b", "**"),
            get_typo_cleaner("i", "*"),
            get_typo_cleaner("c", "`"),

            Converter(pattern=r'\[i\]\*\*([^\n\r\*\`]*?)\*\*\[/i\]',
                      repl=r"***\1***",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)imp\]',
                      repl=r"[\1important]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)warn\]',
                      repl=r"[\1warning]",
                      flags=re.IGNORECASE),
        ]

    def __call__(self, markdown, field, locale, wiki_object):
        result = markdown
        for cleaner in self.cleaners:
            result = cleaner(result)

        d = difflib.Differ()
        diff = d.compare(markdown.split("\n"), result.split("\n"))
        for dd in diff:
            if dd[0] != " ":
                print(dd)

        return result


class LtagCleaner(MarkdownProcessor):
    _tests = [
        {
            "source": "L#|1:2",
            "result": "L# | 1:2"
        },
        {
            "source": "L#|1::2",
            "result": "L# | 1 | 2"
        },
        {
            "source": "L#:1::2",
            "result": "L# | 1 | 2"
        },
        {
            "source": "L#::1::2||3:: ::5|6| |7::8:aussi 8|9",
            "result": "L# | 1 | 2 | 3 |  | 5 | 6 |  | 7 | 8:aussi 8 | 9"
        },
    ]

    def do_tests(self):
        for test in self._tests:
            result = self(test["source"], "", "", "")
            if result != test["result"]:
                print("source   ", test["source"])
                print("expected ", test["result"])
                print("result   ", result)
                print()

    def __init__(self):
        self.modifiers = []

        newline_converter = Converter(pattern=r'(\n[LR]#)([^\n]+)\n(|.|[^RL\n][^#\n][^\n]*)(\n[LR]#|\n)',
                                      repl=r"\1\2<br>\3\4",
                                      flags=re.IGNORECASE)

        # replace leanding `:` by `|`
        leading_converter = Converter(pattern=r'^([LR]#)([^\n \|\:]*) *\:+',
                                      repl=r"\1\2 |",
                                      flags=re.IGNORECASE)

        # replace multiple consecutives  `:` or  `|` by `|`
        multiple_converter = Converter(pattern=r' *([\:\|]{2,}|\|) *',
                                       repl=r" | ",
                                       flags=re.IGNORECASE)

        def modifier(markdown):
            lines = markdown.split("\n")
            result = []

            for line in lines:
                if line.startswith("L#") or line.startswith("R#"):
                    line = leading_converter(line)
                    line = multiple_converter(line)

                result.append(line)

            return "\n".join(result)

        self.modifiers.append(newline_converter)
        self.modifiers.append(modifier)

    def __call__(self, markdown, field, locale, wiki_object):
        result = "\n" + markdown

        for modifier in self.modifiers:
            result = modifier(result)

        result = result[1:]

        # d = difflib.Differ()
        # diff = d.compare(markdown.split("\n"), result.split("\n"))
        # for dd in diff:
        #     if dd[0] != " ":
        #         print(dd)

        return result