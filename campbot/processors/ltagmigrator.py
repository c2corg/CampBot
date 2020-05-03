from .core import MarkdownProcessor, Converter
import re


class LtagCleaner(MarkdownProcessor):
    ready_for_production = True
    comment = "Simplify L# syntax"

    def init_modifiers(self):
        self.modifiers = []

        newline_converters = [
            Converter(
                pattern=r"\nL#(.*)\n\nL#", repl=r"\nL#\1\nL#", flags=re.IGNORECASE
            ),
            Converter(
                pattern=r"\nR#(.*)\n\nR#", repl=r"\nR#\1\nR#", flags=re.IGNORECASE
            ),
        ]

        # replace leading `:` by `|`
        leading_converter = Converter(
            pattern=r"^([LR]#)([^\n \|\:]*)( *)\:+",
            repl=r"\1\2\3|",
            flags=re.IGNORECASE,
        )

        # replace no first sep by `|`
        no_leading_converter = Converter(
            pattern=r"^([LR]#)([^\n \|\:]*)( +)([^\:\|\ ])",
            repl=r"\1\2\3|\4",
            flags=re.IGNORECASE,
        )

        # replace multiple consecutives  `:` or  `|` by `|`
        multiple_converter = Converter(
            pattern=r"( *)(<br>)?( *)([\:\|]{2,}|\|)( *)(<br>)?( *)",
            repl=r"\1\3|\5\7",
            flags=re.IGNORECASE,
        )

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


def _get_ltag_pattern():
    """
    Build the big ugly fat regexp for L# numbering. It's based on named
    patterns : (P?<pattern_name>pattern) and decomposed part by part.

    Please have a look on
    https://forum.camptocamp.org/t/question-l/207148/69
    """
    p = "(?P<{}>{})".format

    # small patterns used more than once
    raw_label = r"[a-zA-Z'\"][a-zA-Z'\"\d_]*|_"
    raw_offset = r"[+\-]?\d*"

    # let's build multi pitch pattern, like L#-+3 or L#12-+4ter
    multi_pitch_label = p("multi_pitch_label", raw_label)
    first_offset = p("first_offset", raw_offset)
    last_offset = p("last_offset", raw_offset)
    first_pitch = p("first_pitch", first_offset + multi_pitch_label + "?")
    last_pitch = p("last_pitch", last_offset)
    multi_pitch = p("multi_pitch", first_pitch + "?-" + last_pitch)

    # mono pitch
    mono_pitch_label = p("mono_pitch_label", raw_label)
    mono_pitch_value = p("mono_pitch_value", r"\+?\d*")
    mono_pitch = p("mono_pitch", mono_pitch_value + mono_pitch_label + "?")

    local_ref = p("local_ref", r"!")

    pitch = "(" + multi_pitch + "|" + mono_pitch + ")"
    numbering = p("numbering", pitch + local_ref + "?")

    text_in_the_middle = p("text_in_the_middle", "~")
    header = p("header", "=")

    typ = p("type", "^[LR]")

    text = "(" + header + "|" + text_in_the_middle + "|" + numbering + ")"

    return p("ltag", typ + "#" + text)


class LTagNumbering(object):
    """
    The aim of this class is to store and handle everything about numbering.
    This class replaces markdown L# values by numeric values, and changes
    it's state if necessary.

    This class owns a one way switch called "supported", initially set to
    True. If it sees an unsupported pattern, it toggles it to False and
    convert any L# pattern to <code>L#Whatever</code>
    """

    # regular expression used to perform the syntax analysis
    PATTERN = re.compile(_get_ltag_pattern())

    # helper for final formatting
    FORMAT = "{type}#{text}".format
    FORMAT_UNMATCHED = "{}".format

    def __init__(self):

        # Values for relative patterns
        self.value = {"R": 0, "L": 0}

        # One way switch
        self.supported = True

        # If no relative pattern is present, then labels are allowed
        # As now, the only relative pattern handled is a simple L#
        self.allow_labels = True

        # if numbering contains a label, then relatives patterns
        # are no more allowed anymore
        self.contains_label = False

    def handle_unmatched(self, match):
        return match.group(0)

    def compute(self, markdown, row_type, is_first_cell):
        """
        Replace all L# patterns by good numbering values. it tests that first
        cell perfectly match pattern. If an error occurs or a unsupported
        pattern is found, it will returns raw pattern inside a <code/> block
        """
        assert markdown

        if not self.supported:
            return self.PATTERN.sub(self.handle_unmatched, markdown)

        # this function does not belong to self, because it
        # must access to row_type and is_first_cell
        def handle_match(match):

            assert match.group("local_ref") is None, "Not yet supported"

            if match.group("header") is not None:  # means L#=
                result = match.group(0)

            elif match.group("text_in_the_middle") is not None:
                result = match.group(0)

            elif match.group("multi_pitch") is not None:
                result = self.handle_multipitch(match, is_first_cell)

            elif match.group("mono_pitch") is not None:
                result = self.handle_monopitch(match, row_type, is_first_cell)

            else:
                raise NotImplementedError("Should not happen!?")

            return result

        try:
            return self.PATTERN.sub(handle_match, markdown)

        except (NotImplementedError, AssertionError):
            self.supported = False
            return self.PATTERN.sub(self.handle_unmatched, markdown)

    def compute_label(self, raw_label):
        """
        Get L# label, and check supported use case
        """

        assert raw_label is None

        return ""

    def handle_multipitch(self, match, is_first_cell):
        """
        Can be :

            L#1-4
            L#1bis-4
        """
        label = self.compute_label(match.group("multi_pitch_label"))

        typ = match.group("type")
        first_offset = match.group("first_offset")
        last_offset = match.group("last_offset")

        if len(first_offset) == 0 or first_offset == "+":
            first_offset = "+1"

        if first_offset[0] == "+":
            assert first_offset[1:].isdigit()
            first_offset = self.value[typ] + int(first_offset[1:])
            first_offset = str(first_offset)

        assert first_offset.isdigit(), "Not yet supported"
        self.value[typ] = int(first_offset)

        if last_offset[0] == "+":
            assert last_offset[1:].isdigit()
            last_offset = self.value[typ] + int(last_offset[1:])
            last_offset = str(last_offset)

        assert last_offset.isdigit(), "Not yet supported"

        if is_first_cell:  # first cell impacts numbering
            self.value[typ] = int(last_offset)

        text = "".join((first_offset, label, "-", last_offset, label))

        return self.FORMAT(type=typ, text=text)

    def handle_monopitch(self, match, row_type, is_first_cell):
        """
        Can be :

            L#
            L#12
            L#13bis
        """

        label = self.compute_label(match.group("mono_pitch_label"))

        typ = match.group("type")
        value = match.group("mono_pitch_value")

        if value.isdigit():
            return self.handle_monopitch_value(typ, is_first_cell, value, label)

        elif len(value) == 0:
            old_value = self.value[typ if is_first_cell else row_type]

            return self.handle_monopitch_offset(typ, is_first_cell, old_value)

        else:
            assert value[0] == "+"
            value = value[1:]
            if len(value) == 0:
                value = "1"

            assert value.isdigit()

            old_value = self.value[typ if is_first_cell else row_type]
            return self.handle_monopitch_offset(
                typ, is_first_cell, old_value, int(value)
            )
            # may be
            # L#+12  (offset)
            # L#+12bis (offset with label)

    def handle_monopitch_value(self, typ, is_first_cell, value, label):
        # Fixed number : L#12
        # and label :    L#12bis

        if is_first_cell:  # first cell impacts numbering
            self.value[typ] = int(value)

        return self.FORMAT(type=typ, text=value + label)

    def handle_monopitch_offset(self, typ, is_first_cell, old_value, offset=1):
        # Simple use case : L#
        self.allow_labels = False
        assert not self.contains_label, "Not yet supported"

        value = old_value

        if is_first_cell:  # first cell impacts numbering
            value += offset
            self.value[typ] = value

        return self.FORMAT(type=typ, text=str(value))


class LtagMigrator(MarkdownProcessor):
    ready_for_production = True
    comment = "Convert L# to V6"

    def init_modifiers(self):
        self.modifiers = [self.convert]

    def convert(self, markdown):
        numbering = LTagNumbering()

        result = []
        for row in markdown.split("\n"):
            if row.startswith("L#") or row.startswith("R#"):
                row_type = row[0]
                row = numbering.compute(row, row_type=row_type, is_first_cell=True)

            result.append(row)

        if not numbering.supported:
            return markdown

        return "\n".join(result)
