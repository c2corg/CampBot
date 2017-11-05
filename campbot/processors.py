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
    modifiers = []
    ready_for_production = False
    comment = NotImplemented

    def __call__(self, markdown, field, locale, wiki_object):
        result = self.modify(markdown)

        d = difflib.Differ()
        diff = d.compare(markdown.replace("\r", "").split("\n"), result.replace("\r", "").split("\n"))
        for dd in diff:
            if dd[0] != " ":
                print(dd)

        return result

    def modify(self, markdown):
        result = "\n" + markdown

        for modifier in self.modifiers:
            result = modifier(result)

        result = result[1:]
        return result


class BBCodeRemover(MarkdownProcessor):
    ready_for_production = True
    comment = "Replace BBcode by Markdown"

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

        self.modifiers = [
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


class LtagCleaner(MarkdownProcessor):
    ready_for_production = False
    comment = "Simplify L# syntax"

    _tests = [
        {
            "source": "L#{} | 1 | 2\nL# | 1 | 2\n\nautre texte",
            "result": "L#{} | 1 | 2\nL# | 1 | 2\n\nautre texte"
        },
        {
            "source": "L#{} | 1 | 2\n\nL# | 1 | 2\n",
            "result": "L#{} | 1 | 2\nL# | 1 | 2\n"
        },
        {
            "source": "L#{} | 1\n2 | 2\nL# | 1 | 2\n\n\nautre texte",
            "result": "L#{} | 1<br>2 | 2\nL# | 1 | 2\n\n\nautre texte",
        },
        {
            "source": "L#{} |\n 12 | 2\nL#{} | 1 \n| 2\n",
            "result": "L#{} | 12 | 2\nL#{} | 1 | 2\n"
        },
        {
            "source": "L#{} | 1 L# 2 | 2\nL#{} | 1 | 2\n3\n",
            "result": "L#{} | 1 L# 2 | 2\nL#{} | 1 | 2<br>3\n"
        },
        {
            "source": "L#{} | 12 | 2\nL#{} | 1 | 2\n3\n\n4",
            "result": "L#{} | 12 | 2\nL#{} | 1 | 2<br>3\n\n4"
        },
        {
            "source": "L#{}:1::2\n##Titre",
            "result": "L#{}|1|2\n##Titre"
        },
        {
            "source": "L#{} |1::2",
            "result": "L#{} |1|2"
        },
        {
            "source": "L#{}:1::2",
            "result": "L#{}|1|2"
        },
        {
            "source": "L#{}|1:2::3||R#4||||5::::6",
            "result": "L#{}|1:2|3|R#4|5|6"
        },
        {
            "source": "L#{} 1:2",
            "result": "L#{} |1:2"
        },
        {
            "source": "L#{}|1::2",
            "result": "L#{}|1|2"
        },
        {
            "source": "L#{}::1::2||3:: ::5|6| |7::8:aussi 8|9",
            "result": "L#{}|1|2|3| |5|6| |7|8:aussi 8|9"
        },
        {
            "source": "L#~ plein ligne !:: \n| fds : \n\n| {} a la fin",
            "result": "L#~ plein ligne !:: <br>| fds : \n\n| {} a la fin",
        },
        {
            "source": "L#{} || [[touche/pas|au lien]] : stp::merci ",
            "result": "L#{} | [[touche/pas|au lien]] : stp|merci "
        },
    ]

    _numbering_postfixs = ["", "12", "+3", "+", "-25", "-+2", "+2-+1", "bis", "bis2", "*5bis", "+5bis", "_", "+bis",
                           "''", "+''", "!", "2!", "+2!", "="]

    def do_tests(self):
        def do_test(source, expected):
            result = self.modify(source)
            if result != expected:
                print("source   ", repr(source))
                print("expected ", repr(expected))
                print("result   ", repr(result))
                print()

        for postfix in self._numbering_postfixs:
            for test in self._tests:
                source = test["source"].format(postfix, postfix)
                expected = test["result"].format(postfix, postfix)
                do_test(source, expected)

    def __init__(self):
        self.modifiers = []

        newline_converters = [
            Converter(pattern=r'\nL#(.*)\n\nL#',
                      repl=r"\nL#\1\nL#",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\nR#(.*)\n\nR#',
                      repl=r"\nR#\1\nR#",
                      flags=re.IGNORECASE),
        ]

        # replace leading `:` by `|`
        leading_converter = Converter(pattern=r'^([LR]#)([^\n \|\:]*)( *)\:+',
                                      repl=r"\1\2\3|",
                                      flags=re.IGNORECASE)

        # replace no first sep by `|`
        no_leading_converter = Converter(pattern=r'^([LR]#)([^\n \|\:]*)( +)([^\:\|\ ])',
                                         repl=r"\1\2\3|\4",
                                         flags=re.IGNORECASE)

        # replace multiple consecutives  `:` or  `|` by `|`
        multiple_converter = Converter(pattern=r'( *)(<br>)?( *)([\:\|]{2,}|\|)( *)(<br>)?( *)',
                                       repl=r"\1\3|\5\7",
                                       flags=re.IGNORECASE)

        def modifier(markdown):
            markdown = markdown.replace("\r\n", "\n")
            markdown = markdown.replace("\r", "\n")

            for converter in newline_converters:
                markdown = converter(markdown)

            lines = markdown.split("\n")
            result = []

            last_line_is_ltag = False
            for line in lines:
                if line.startswith("L#") or line.startswith("R#"):
                    result.append(line)
                    last_line_is_ltag = True

                elif line.startswith("#") or line == "":
                    result.append(line)
                    last_line_is_ltag = False

                elif not last_line_is_ltag:
                    last_line_is_ltag = False
                    result.append(line)

                else:  # last_line_is_ltag is true here
                    result[len(result) - 1] += "<br>" + line

            markdown = "\n".join(result)

            lines = markdown.split("\n")
            result = []

            for line in lines:
                if (line.startswith("L#") or line.startswith("R#")) and line[2] != "~":
                    line = leading_converter(line)
                    line = no_leading_converter(line)
                    line = multiple_converter(line)

                result.append(line)

            return "\n".join(result)

        self.modifiers.append(modifier)
