from __future__ import print_function, unicode_literals, division

import difflib
import re
from .dump import get_document_types

__all__ = ['MarkdownProcessor', 'BBCodeRemover', 'LtagCleaner', 'BBCodeRemover2']


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

    def __call__(self, markdown, field, locale, wiki_object):
        result = self.modify(markdown)

        if self.ready_for_production:
            d = difflib.Differ()
            diff = d.compare(markdown.replace("\r", "").split("\n"),
                             result.replace("\r", "").split("\n"))
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

    _tests = [
        {
            "source": "*[Voir la discussion sur le forum.](#t158106)*",
            "expected": "*[Voir la discussion sur le forum.](https://www.camptocamp.org/forums/viewtopic.php?id=158106)*",
        },
        {
            "source": "[col][col 50 left]",
            "expected": "",
        },
        {
            "source": "x[hr]",
            "expected": "x\n----\n",
        },
        {
            "expected": "{#coucou}",
            "source": '<span id="coucou"></span>',
        },
        {
            "source": "[center]coucou[/center]",
            "expected": "<center>coucou</center>",
        },
        {
            "source": "[acr=1 goujon et 2-3 lunules]1g..3l[/acr]",
            "expected": '<abbr title="1 goujon et 2-3 lunules">1g..3l</abbr>',
        },
        {
            "source": "L#~ | coucou",
            "expected": "L#~ coucou",
        },
        {
            "source": "L# | gne\nL#~|coucou",
            "expected": "L# | gne\nL#~ coucou",
        },
        {
            "source": "L#~|   coucou\nL# | ~",
            "expected": "L#~ coucou\nL# | ~",
        },
        {
            "source": "L#~ |||| A",
            "expected": "L#~ A",
        },
        {
            "source": "un texte en [b]gras [/b]et un en [i]italique[/i] [i][/i] ",
            "expected": "un texte en **gras** et un en *italique*  ",
        },
        {
            "source": "un texte en [b][i]gras et italique[/i][/b]",
            "expected": "un texte en ***gras et italique***",
        },
        {
            "source": "[center][b]outside![/b][/center]",
            "expected": "**<center>outside!</center>**",
        },
        {
            "source": "[url=http:google.fr][i]outside![/i][/url]",
            "expected": "*[outside!](http:google.fr)*",
        },
        {
            "source": "[b]\r\ngrep!\r\n[/b]",
            "expected": "\r\n**grep!**\r\n",
        },
        {
            "source": "#c coucou ##c s",
            "expected": "# coucou ##c s",
        },
        {
            "source": "line\n####c coucou ##c s",
            "expected": "line\n#### coucou ##c s",
        },
        {
            "source": "###coucou",
            "expected": "###coucou",
        },
        {
            "source": "###C bien",
            "expected": "###C bien",
        },
        {
            "source": "[url=]http://www.zone-di-tranquillita.ch/[/url]",
            "expected": "http://www.zone-di-tranquillita.ch/ "
        },
        {
            "source": "[url]http://www.google.com[/url]",
            "expected": "http://www.google.com "
        },
        {
            "source": "[url]http://www.google.com[/url] x [url]http://www.google2.com[/url]",
            "expected": "http://www.google.com  x http://www.google2.com "
        },
        {
            "source": "[url=http://www.google.com]google[/url]",
            "expected": "[google](http://www.google.com)",
        },
        {
            "source": "[url=http://www.google.com]google[/url] et [url=http://www.google2.com]google2[/url]",
            "expected": "[google](http://www.google.com) et [google2](http://www.google2.com)"
        },
        {
            "source": "[url]http://www.google.com?a=b&c=d[/url] and [url=http://www.google.com?a=b!c]pas touche[/url]",
            "expected": "http://www.google.com?a=b&c=d  and [pas touche](http://www.google.com?a=b!c)"
        },
        {
            "source": "[url]http://www.google.com?a=b;d[/url] et [url]pas.touche.fr[/url]",
            "expected": "http://www.google.com?a=b;d  et [url]pas.touche.fr[/url]"
        },
        {
            "source": "[url]http://www.google.com?a=b&c=d[/url] x [url]http://www.google2.com?a=b&c=d[/url]",
            "expected": "http://www.google.com?a=b&c=d  x http://www.google2.com?a=b&c=d "
        },
        {
            "source": "[url=http://www.google.com?a=b&c=d]google[/url]",
            "expected": "[google](http://www.google.com?a=b&c=d)",
        },
        {
            "source": "[url=http://www.google.com?a=b&c=d]go[/url] et [url=http://www.google2.com?a=b&c=d]o[/url]",
            "expected": "[go](http://www.google.com?a=b&c=d) et [o](http://www.google2.com?a=b&c=d)"
        },
        {
            "source": "[email]dev@camptocamp.org[/email]",
            "expected": "[dev@camptocamp.org](mailto:dev@camptocamp.org)"
        },
        {
            "source": "[email=dev@camptocamp.org]email[/email]",
            "expected": "[email](mailto:dev@camptocamp.org)"
        },
        {
            "source": "[url=]http://www.zone-di-tranquillita.ch/[/url]",
            "expected": "http://www.zone-di-tranquillita.ch/ "
        },
        {
            "source": "[url]http://www.google.com?a=1&b=2[/url]",
            "expected": "http://www.google.com?a=1&b=2 "
        },
        {
            "source": "[url]http://www.google.com?a=1&b=2[/url] x [url]www.google2.com[/url]",
            "expected": "http://www.google.com?a=1&b=2  x www.google2.com "
        },
        {
            "source": "[url=http://www.google.com?a=1&b=2]google[/url]",
            "expected": "[google](http://www.google.com?a=1&b=2)",
        },
        {
            "source": "[url=http://www.google.com]google[/url] et [url=http://www.google2.com]google2[/url]",
            "expected": "[google](http://www.google.com) et [google2](http://www.google2.com)"
        },
        {
            "source": "[url]http://www.google.com?a=b&c=d[/url] and [url=http://www.google.com?a=b!c]pas touche[/url]",
            "expected": "http://www.google.com?a=b&c=d  and [pas touche](http://www.google.com?a=b!c)"
        },
        {
            "source": "[url]pas.touche.fr[/url]",
            "expected": "[url]pas.touche.fr[/url]"
        },
        {
            "source": "[url=http://www.google.com?a=b&c=d]google[/url]",
            "expected": "[google](http://www.google.com?a=b&c=d)",
        },
        {
            "source": "[url=http://www.google.com?a=b&c=d]google[/url]",
            "expected": "[google](http://www.google.com?a=b&c=d)",
        },
        {
            "source": "[sub]xx[/sub]",
            "expected": "<sub>xx</sub>",
        },
        {
            "source": "[sup]xx[/sup]",
            "expected": "<sup>xx</sup>",
        },
        {
            "source": "[s]xx[/s]",
            "expected": "<s>xx</s>",
        },
    ]

    def init_modifiers(self):
        def get_typo_cleaner(bbcode_tag, markdown_tag):

            def invalid_killer(markdown):
                opener = len(markdown.split("[" + bbcode_tag + "]"))
                closer = len(markdown.split("[/" + bbcode_tag + "]"))

                if opener == 1 and closer > 1:
                    markdown = markdown.replace("[/" + bbcode_tag + "]", "")

                if opener > 1 and closer == 1:
                    markdown = markdown.replace("[" + bbcode_tag + "]", "")

                return markdown

            converters = [

                Converter(pattern=r"\[ *url *\]",
                          repl=r"[url]",
                          flags=re.IGNORECASE
                          ),

                Converter(pattern=r"\[ *url *= *",
                          repl=r"[url=",
                          flags=re.IGNORECASE
                          ),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]\[/' + bbcode_tag + '\]',
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

                Converter(
                    pattern=r'\[center] *\[' + bbcode_tag + r'\]([^\n\r\*\`]*?)\[/' + bbcode_tag + '\] *\[/center]',
                    repl=markdown_tag + r"[center]\1[/center]" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[url=(.*?)] *\[' + bbcode_tag + r'\]([^\n\r\*\`]*?)\[/' + bbcode_tag + '\] *\[/url]',
                    repl=markdown_tag + r"[url=\1]\2[/url]" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]([^\n\r\*\`]*?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]([^\n\r\*\`]+?)\r?\n([^\n\r\*\`]+?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1\n\2" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE),

                Converter(
                    pattern=r'\[' + bbcode_tag + r'\]' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\r?\n' +
                            r'([^\n\r\*\`]+?)\[/' + bbcode_tag + '\]',
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE),

                #   invalid_killer,
            ]

            def result(markdown):
                for converter in converters:
                    markdown = converter(markdown)

                return markdown

            return result

        self.modifiers = [
            get_typo_cleaner("b", "**"),
            get_typo_cleaner("i", "*"),

            Converter(pattern=r'\[i\]\*\*([^\n\r\*\`]*?)\*\*\[/i\]',
                      repl=r"***\1***",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)imp\]',
                      repl=r"[\1important]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)warn\]',
                      repl=r"[\1warning]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'(^|\n)(#+)c +',
                      repl=r"\1\2 "),

            Converter(pattern=r'\nurl=',
                      repl=r"\n[url=",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\nurl]',
                      repl=r"\n[url]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[ *url *= *\]',
                      repl=r"[url]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[ *url *= *',
                      repl=r"[url=",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[\\url\]',
                      repl=r"[/url]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[urlhttp',
                      repl=r"[url]http",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[url=?\] *(http|www)(.*?)\[/url\]',
                      repl=r"\1\2 ",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[url\=(.*?)\]\[\/url\]',
                      repl=r" \1 ",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[url\=(.*?)\](.*?)\[\/url\]',
                      repl=r"[\2](\1)",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[email\](.*?)\[/email\]',
                      repl=r"[\1](mailto:\1)",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[email\=(.*?)\](.*?)\[\/email\]',
                      repl=r"[\2](mailto:\1)",
                      flags=re.IGNORECASE),

            Converter(pattern=r"(\n|^)L#\~ *\|+ *",
                      repl=r"\1L#~ "),

            Converter(pattern=r"\(#t(\d+)\)",
                      repl=r"(https://www.camptocamp.org/forums/viewtopic.php?id=\1)"),

            Converter(pattern=r'\[(/?)sub\]',
                      repl=r"<\1sub>",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)sup\]',
                      repl=r"<\1sup>",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)s\]',
                      repl=r"<\1s>",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[acr=([\w \.-]+)\]([\w \.]+)\[/acr\]',
                      repl=r'<abbr title="\1">\2</abbr>',
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[(/?)center]',
                      repl=r"<\1center>",
                      flags=re.IGNORECASE),

            Converter(pattern=r'<span id="([\w-]+)"></span>',
                      repl=r'{#\1}',
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n?\[hr/?\]\n?',
                      repl=r"\n----\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[[tT]oc ?([\d])?( right| left)?\]',
                      repl=r"[toc]",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[/? *col *\d* *(left|right)? *\d* *\]',
                      repl=r"",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_1 */\]',
                      repl=r":skitouring:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_6 */\]',
                      repl=r":hiking:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_2 */\]',
                      repl=r":snow_ice_mixed:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_3 */\]',
                      repl=r":mountain_climbing:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_4 */\]',
                      repl=r":rock_climbing:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_5 */\]',
                      repl=r":ice_climbing:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_7 */\]',
                      repl=r":snowshoeing:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto activity_8 */\]',
                      repl=r":paragliding:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_books */\]',
                      repl=r":book:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_maps */\]',
                      repl=r":map:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto action_report */\]',
                      repl=r"",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_summits */\]',
                      repl=r":summit:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_huts */\]',
                      repl=r":hut:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_products */\]',
                      repl=r":local_product:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_parkings */\]',
                      repl=r":parking:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_routes */\]',
                      repl=r":motorway:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\[picto picto_users */\]',
                      repl=r":mens:",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n!!! \\6\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*',
                      repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n!!! \\6\n!!! \\7\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n!!!! \\2\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n!!!! \\5\n\n",
                      flags=re.IGNORECASE),

            Converter(pattern=r'\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*',
                      repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n!!!! \\5\n!!!! \\6\n\n",
                      flags=re.IGNORECASE),
        ]


class LtagCleaner(MarkdownProcessor):
    ready_for_production = True
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

    _numbering_postfixs = ["", "12", "+3", "+", "-25", "-+2", "+2-+1", "bis",
                           "bis2", "*5bis", "+5bis", "_", "+bis",
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

    def init_modifiers(self):
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
        no_leading_converter = Converter(
            pattern=r'^([LR]#)([^\n \|\:]*)( +)([^\:\|\ ])',
            repl=r"\1\2\3|\4",
            flags=re.IGNORECASE)

        # replace multiple consecutives  `:` or  `|` by `|`
        multiple_converter = Converter(
            pattern=r'( *)(<br>)?( *)([\:\|]{2,}|\|)( *)(<br>)?( *)',
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


class ColorAndUnderlineRemover(MarkdownProcessor):
    ready_for_production = True
    comment = "Remove color and u tags"

    _tests = [
        {
            "source": "test [u]underlines[/u] and [color=#FFdd1E]color[/color] et [color=red]color[/color]",
            "expected": "test underlines and color et color"
        },
    ]

    def init_modifiers(self):
        self.modifiers = []
        self.modifiers.append(
            Converter(pattern=r'\[/?(color|u)(=#?[a-zA-Z0-9]{3,10})?\]',
                      repl=r"",
                      flags=re.IGNORECASE), )


class MarkdownCleaner(MarkdownProcessor):
    ready_for_production = True
    comment = "Clean markdown"

    _tests = [
        {
            "source": "[](http://link)x",
            "expected": "http://link x",
        },
        {
            "source": "cou[](http://link)x",
            "expected": "cou http://link x",
        },
        {
            "source": "x[img",
            "expected": "x\n[img",
        },
        {
            "source": "\n\nx\n\nx\n\n",
            "expected": "x\n\nx",
        }
    ]

    def init_modifiers(self):
        self.modifiers = [
            Converter(pattern=r"\n\[ *\]\((http[^\n ]+)\) *",
                      repl=r"\n\1 "),
            Converter(pattern=r"^\[ *\]\((http[^\n ]+)\) *",
                      repl=r"\1 "),
            Converter(pattern=r" *\[ *\]\((http[^\n ]+)\) *",
                      repl=r" \1 "),
            Converter(pattern=r"\n\[ *\]\(([^\n ]+)\) *",
                      repl=r"\nhttp://\1 "),
            Converter(pattern=r"^\[ *\]\(([^\n ]+)\) *",
                      repl=r"http://\1 "),
            Converter(pattern=r" *\[ *\]\(([^\n ]+)\) *",
                      repl=r" http://\1 "),

            Converter(pattern=r"([^\n])\[img",
                      repl=r"\1\n[img"),
        ]


class InternalLinkCorrector(MarkdownProcessor):
    ready_for_production = True
    comment = "Fix internal wiki link"

    _tests = [
        {
            "source": "[[786432|patate]]",
            "expected": "[[routes/786432|patate]]"
        },
        {
            "source": "[[/routes/786432|patate]]",
            "expected": "[[routes/786432|patate]]"
        },
        {
            "source": "[[http://www.camptocamp.org/articles/106859/fr|cotation de randonnée pédestre]]",
            "expected": "[[articles/106859/fr|cotation de randonnée pédestre]]"
        },
        {
            "source": "[[http://www.camptocamp.org/routes/173371/it/via-bartesaghi-iii-torrione|Via Bartesaghi]] ",
            "expected": "[[routes/173371/it/via-bartesaghi-iii-torrione|Via Bartesaghi]] "
        },
        {
            "source": "[[http://www.camptocamp.org/images/19796/fr/|photo]]",
            "expected": "[[images/19796/fr/|photo]]"
        },
        {
            "source": "[[http://www.camptocamp.org/routes/186949/fr/presles-approches-descentes-presles#secteur-fhara-kiri|Voir approches & descentes]]. ",
            "expected": "[[routes/186949/fr/presles-approches-descentes-presles#secteur-fhara-kiri|Voir approches & descentes]]. "
        },

    ]

    def __init__(self):
        self.types = get_document_types()
        super().__init__()

    def init_modifiers(self):
        self.modifiers = [self.fixer_no_type, self.fixer_false_internal, self.fixer_slash_internal]

    def fixer_no_type(self, markdown):
        def repl(m):
            doc_id = int(m.group(1))
            if doc_id not in self.types:
                return "[[" + str(doc_id) + "|"

            tp = {
                "r": "routes",
                "i": "images",
                "a": "areas",
                "w": "waypoints",
                "b": "books",
                "c": "articles",
            }[self.types[doc_id]]

            return "[[" + tp + "/" + str(doc_id) + "|"

        return re.sub(r'\[\[ */? *(\d+)\|', repl, markdown)

    def fixer_false_internal(self, markdown):
        def repl(m):
            tp = m.group(1)
            doc_id = m.group(2)
            after = m.group(3)

            tp = "waypoints" if tp in ("summits", "sites", "huts", "parkings") else tp
            tp = "profiles" if tp in ("users",) else tp

            return "[[" + tp + "/" + doc_id + after + "|"

        return re.sub(
            r'\[\[ *https?://www.camptocamp.org/(parkings|users|books|articles|routes|waypoints|images|summits|sites|huts|outings)/(\d+)([\w\-/#]*)\|',
            repl,
            markdown)

    def fixer_slash_internal(self, markdown):
        def repl(m):
            tp = m.group(1)
            doc_id = m.group(2)
            after = m.group(3)

            tp = "waypoints" if tp in ("summits", "sites", "huts", "parkings") else tp
            tp = "profiles" if tp in ("users",) else tp

            return "[[" + tp + "/" + doc_id + after + "|"

        return re.sub(
            r'\[\[ */(parkings|users|books|articles|routes|waypoints|images|summits|sites|huts|outings)/(\d+)([\w\-/#]*)\|',
            repl,
            markdown)
