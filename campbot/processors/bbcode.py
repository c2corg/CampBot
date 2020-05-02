from .core import MarkdownProcessor, Converter
import re


class ColorAndUnderlineRemover(MarkdownProcessor):
    ready_for_production = True
    comment = "Remove color and u tags"

    def init_modifiers(self):
        self.modifiers = []
        self.modifiers.append(
            Converter(
                pattern=r"\[/?(color|u)(=#?[a-zA-Z0-9]{3,10})?\]",
                repl=r"",
                flags=re.IGNORECASE,
            ),
        )


class BBCodeRemover(MarkdownProcessor):
    ready_for_production = True
    comment = "Replace BBcode by Markdown"

    def init_modifiers(self):
        def get_typo_cleaner(bbcode_tag, markdown_tag):
            converters = [
                Converter(pattern=r"\[ *url *\]", repl=r"[url]", flags=re.IGNORECASE),
                Converter(pattern=r"\[ *url *= *", repl=r"[url=", flags=re.IGNORECASE),
                Converter(
                    pattern=r"\[" + bbcode_tag + r"\]\[/" + bbcode_tag + r"\]",
                    repl=r"",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\n *\[" + bbcode_tag + r"\] *",
                    repl=r"\n[" + bbcode_tag + r"]",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\[" + bbcode_tag + r"\] +",
                    repl=r" [" + bbcode_tag + r"]",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r" +\[/" + bbcode_tag + r"\]",
                    repl=r"[/" + bbcode_tag + r"] ",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\r\n\[/" + bbcode_tag + r"\]",
                    repl=r"[/" + bbcode_tag + r"]\r\n",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\[" + bbcode_tag + r"\] *\r\n([^\*\#]?)",
                    repl=r"\r\n[" + bbcode_tag + r"]\1",
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\[center] *\["
                    + bbcode_tag
                    + r"\]([^\n\r\*\`]*?)\[/"
                    + bbcode_tag
                    + r"\] *\[/center\]",
                    repl=markdown_tag + r"[center]\1[/center]" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\[url=(.*?)] *\["
                    + bbcode_tag
                    + r"\]([^\n\r\*\`]*?)\[/"
                    + bbcode_tag
                    + r"\] *\[/url\]",
                    repl=markdown_tag + r"[url=\1]\2[/url]" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]([^\n\r\*\`]*?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]([^\n\r\*\`]+?)\r?\n([^\n\r\*\`]+?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1\n\2" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
                Converter(
                    pattern=r"\["
                    + bbcode_tag
                    + r"\]"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\r?\n"
                    + r"([^\n\r\*\`]+?)\[/"
                    + bbcode_tag
                    + r"\]",
                    repl=markdown_tag + r"\1\n\2\n\3" + markdown_tag,
                    flags=re.IGNORECASE,
                ),
            ]

            def result(markdown):
                for converter in converters:
                    markdown = converter(markdown)

                return markdown

            return result

        self.modifiers = [
            get_typo_cleaner("b", "**"),
            get_typo_cleaner("i", "*"),
            Converter(
                pattern=r"\[i\]\*\*([^\n\r\*\`]*?)\*\*\[/i\]",
                repl=r"***\1***",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[(/?)imp\]", repl=r"[\1important]", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[(/?)warn\]", repl=r"[\1warning]", flags=re.IGNORECASE
            ),
            Converter(pattern=r"(^|\n)(#+)c +", repl=r"\1\2 "),
            Converter(pattern=r"\nurl=", repl=r"\n[url=", flags=re.IGNORECASE),
            Converter(pattern=r"\nurl]", repl=r"\n[url]", flags=re.IGNORECASE),
            Converter(pattern=r"\[ *url *= *\]", repl=r"[url]", flags=re.IGNORECASE),
            Converter(pattern=r"\[ *url *= *", repl=r"[url=", flags=re.IGNORECASE),
            Converter(pattern=r"\[\\url\]", repl=r"[/url]", flags=re.IGNORECASE),
            Converter(pattern=r"\[urlhttp", repl=r"[url]http", flags=re.IGNORECASE),
            Converter(
                pattern=r"\[url=?\] *(http|www)(.*?)\[/url\]",
                repl=r"\1\2 ",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[url\=(.*?)\]\[\/url\]", repl=r" \1 ", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[url\=(.*?)\](.*?)\[\/url\]",
                repl=r"[\2](\1)",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[email\](.*?)\[/email\]",
                repl=r"[\1](mailto:\1)",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[email\=(.*?)\](.*?)\[\/email\]",
                repl=r"[\2](mailto:\1)",
                flags=re.IGNORECASE,
            ),
            Converter(pattern=r"(\n|^)L#\~ *\|+ *", repl=r"\1L#~ "),
            Converter(
                pattern=r"\(#t(\d+)\)",
                repl=r"(https://www.camptocamp.org/forums/viewtopic.php?id=\1)",
            ),
            Converter(pattern=r"\[(/?)sub\]", repl=r"<\1sub>", flags=re.IGNORECASE),
            Converter(pattern=r"\[(/?)sup\]", repl=r"<\1sup>", flags=re.IGNORECASE),
            Converter(pattern=r"\[(/?)s\]", repl=r"<\1s>", flags=re.IGNORECASE),
            Converter(
                pattern=r"\[acr=([\w \.-]+)\]([\w \.]+)\[/acr\]",
                repl=r'<abbr title="\1">\2</abbr>',
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[acronym=([\w \.-]+)\]([\w \.]+)\[/acronym\]",
                repl=r'<abbr title="\1">\2</abbr>',
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[(/?)center]", repl=r"<\1center>", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r'<span id="([\w-]+)"></span>',
                repl=r"{#\1}",
                flags=re.IGNORECASE,
            ),
            Converter(pattern=r"\n?\[hr/?\]\n?", repl=r"\n----\n", flags=re.IGNORECASE),
            Converter(
                pattern=r"\[[tT]oc ?([\d])?( right| left)?\]",
                repl=r"[toc]",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[/? *col *\d* *(left|right)? *\d* *\]",
                repl=r"",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_1 */\]|\[img=picto/skitouring.png /\])",
                repl=r":skitouring:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_6 */\]|\[img=picto/hiking.png /\])",
                repl=r":hiking:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_2 */\]|\[img=picto/snow_ice_mixed.png /\])",
                repl=r":snow_ice_mixed:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_3 */\]|\[img=picto/mountain_climbing.png /\])",
                repl=r":mountain_climbing:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_4 */\]|\[img=picto/rock_climbing.png /\])",
                repl=r":rock_climbing:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_5 */\]|\[img=picto/ice_climbing.png /\])",
                repl=r":ice_climbing:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_7 */\]|\[img=picto/snowshoeing.png /\])",
                repl=r":snowshoeing:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"(\[picto activity_8 */\]|\[img=picto/paragliding.png /\])",
                repl=r":paragliding:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[picto picto_books */\]", repl=r":book:", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[picto picto_maps */\]", repl=r":map:", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[picto action_report */\]", repl=r"", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[picto picto_summits */\]",
                repl=r":summit:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[picto picto_huts */\]", repl=r":hut:", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\[picto picto_products */\]",
                repl=r":local_product:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[picto picto_parkings */\]",
                repl=r":parking:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[picto picto_routes */\]",
                repl=r":motorway:",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\[picto picto_users */\]", repl=r":mens:", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n!!! \\6\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[importante?(?: col_50)?\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/importante?\]\n*",
                repl="\n\n!!! \\1\n!!! \\2\n!!! \\3\n!!! \\4\n!!! \\5\n!!! \\6\n!!! \\7\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n!!!! \\2\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n!!!! \\5\n\n",
                flags=re.IGNORECASE,
            ),
            Converter(
                pattern=r"\n*\[warning\][ \n]*([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)\n+([^\n]+)[ \n]*\[/warning\]\n*",
                repl="\n\n!!!! \\1\n!!!! \\2\n!!!! \\3\n!!!! \\4\n!!!! \\5\n!!!! \\6\n\n",
                flags=re.IGNORECASE,
            ),
        ]


class InternalLinkCorrector(MarkdownProcessor):
    ready_for_production = True
    comment = "Fix internal wiki link"

    def __init__(self):
        super(InternalLinkCorrector, self).__init__()

    def init_modifiers(self):
        self.modifiers = [self.fixer_false_internal, self.fixer_slash_internal]

    def fixer_false_internal(self, markdown):
        def repl(m):
            tp = m.group(1)
            doc_id = m.group(2)
            after = m.group(3)

            tp = "waypoints" if tp in ("summits", "sites", "huts", "parkings") else tp
            tp = "profiles" if tp in ("users",) else tp

            return "[[" + tp + "/" + doc_id + after + "|"

        return re.sub(
            r"\[\[ *https?://www.camptocamp.org/(parkings|users|books|articles|routes|waypoints|images|summits|sites|huts|outings)/(\d+)([\w\-/#]*)\|",
            repl,
            markdown,
        )

    def fixer_slash_internal(self, markdown):
        def repl(m):
            tp = m.group(1)
            doc_id = m.group(2)
            after = m.group(3)

            tp = "waypoints" if tp in ("summits", "sites", "huts", "parkings") else tp
            tp = "profiles" if tp in ("users",) else tp

            return "[[" + tp + "/" + doc_id + after + "|"

        return re.sub(
            r"\[\[ */(parkings|users|books|articles|routes|waypoints|images|summits|sites|huts|outings)/(\d+)([\w\-/#]*)\|",
            repl,
            markdown,
        )
