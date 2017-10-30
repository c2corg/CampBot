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

                Converter(pattern=r'\[' + bbcode_tag + r'\]([^\n\r\*\`]*?)\[/' + bbcode_tag + '\]',
                          repl=markdown_tag + r"\1" + markdown_tag,
                          flags=re.IGNORECASE),
            ]

            def result(markdown):
                if '[center][{}]'.format(bbcode_tag) not in markdown:
                    for converter in converters:
                        markdown = converter(markdown)

                return markdown

            return result

        self.cleaners = [
            get_typo_cleaner("b", "**"),
            get_typo_cleaner("i", "*"),
            get_typo_cleaner("c", "`"),
            # get_typo_cleaner("u", "__"),
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
