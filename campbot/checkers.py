# coding: utf-8


"""
## Test contributions validity, and report suspicious contribution.

The main function is `report_recent_changes(bot, days)`, and it will test contributions made in the <days> past days.

A test can inherits one of those two classes:

* `BaseVersionTest()`:
  * implements `test_document(document)`
  * returns `True` if document is OK
* `BaseContributionTest()`:
  * implements `test_contribution(old_doc, new_doc)`
  * returns `True` if going from old_doc to old_doc is OK (for instance, not a too big move)
"""

from __future__ import unicode_literals, print_function, division

from dateutil import parser
import datetime
import re
import logging
from campbot import utils


def _format_delta(delta):
    if delta < 0:
        return "<del>{:+d}</del>".format(delta)

    if delta > 0:
        return "<ins>{:+d}</ins>".format(delta)

    return "**=**"


def _get_diff_url(bot, document, lang, previous_version_id, version_id):
    if not previous_version_id:
        return document.get_url(lang)

    return "{}/{}/diff/{}/{}/{}/{}".format(
        bot.wiki.ui_url,
        document.url_path,
        document.document_id,
        lang,
        previous_version_id,
        version_id,
    )


def _format_timestamp(written_at, with_date):
    return parser.parse(written_at).strftime("%d/%m %H:%M" if with_date else "%H:%M")


class ContributionReport(object):
    def __init__(self, bot, contrib, tests):
        self.contrib = contrib
        self.need_report = False

        self.new = bot.wiki.get_wiki_object_version(
            contrib.document.document_id,
            contrib.document.type,
            contrib.lang,
            contrib.version_id,
        )

        self.old = bot.wiki.get_wiki_object_version(
            contrib.document.document_id,
            contrib.document.type,
            contrib.lang,
            self.new.previous_version_id,
        )

        self.emojis = []

        for test in tests:
            old_is_ok, new_is_ok = test(contrib, self.old, self.new)

            if old_is_ok and not new_is_ok:
                self.emojis.append(test.fail_marker)
                self.need_report = True
            elif not old_is_ok and new_is_ok:
                self.emojis.append(test.success_marker)

        self.delta = self.new.get_locale_length(contrib.lang) if self.new else 0
        self.delta -= self.old.get_locale_length(contrib.lang) if self.old else 0

    def get_multi_report(self, lang, with_date=False):

        result = (
            "  * {timestamp} "
            "([{diff_title}]({diff_url})) **·** "
            "{delta} "
            "{emojis} **·** "
            "[{username}]({user_contrib_url}) →‎ "
            "*{comment}*"
        ).format(
            timestamp=_format_timestamp(self.contrib.written_at, with_date),
            emojis="".join(self.emojis),
            diff_title="diff" if self.new.previous_version_id else "**new**",
            diff_url=self.new.get_diff_url(lang),
            delta=_format_delta(self.delta),
            username=self.contrib.user.name,
            user_contrib_url=self.contrib.user.get_contributions_url(),
            comment=self.contrib.comment if len(self.contrib.comment) else "&nbsp;",
        )

        return result

    def get_mono_report(self, bot, lang, with_date=False):

        title = bot.wiki.get_wiki_object(
            self.new.document.document_id, self.new.document.type
        ).get_title(lang)

        result = (
            "* {timestamp} "
            "([{diff_title}]({diff_url}) | [hist]({hist_url})) **·** "
            "{delta} "
            "{emojis} **·** "
            "[{doc_title}]({doc_url}) **·** "
            "[{username}]({user_contrib_url}) →‎ "
            "*{comment}*"
        ).format(
            timestamp=_format_timestamp(self.contrib.written_at, with_date),
            emojis="".join(self.emojis),
            doc_title=title if len(title) else "*Vide*",
            doc_url=self.new.document.get_url(lang),
            diff_title="diff" if self.new.previous_version_id else "**new**",
            diff_url=self.new.get_diff_url(lang),
            hist_url=self.new.document.get_history_url(self.contrib.lang),
            delta=_format_delta(self.delta),
            username=self.contrib.user.name,
            user_contrib_url=self.contrib.user.get_contributions_url(),
            comment=self.contrib.comment if len(self.contrib.comment) else "&nbsp;",
        )

        return result


class DocumentReport(object):
    def __init__(self, bot, contributions, tests):
        self.need_report = False
        self.sub_reports = []

        for contrib in contributions:
            report = ContributionReport(bot, contrib, tests)
            self.sub_reports.append(report)
            self.need_report = self.need_report or report.need_report

    def get_report(self, bot, lang, with_date=False):
        result = []

        if len(self.sub_reports) == 1:
            result.append(self.sub_reports[0].get_mono_report(bot, lang, with_date))

        else:
            newest_report = self.sub_reports[0]
            oldest_report = self.sub_reports[-1]

            delta = sum([r.delta for r in self.sub_reports])

            title = bot.wiki.get_wiki_object(
                newest_report.new.document.document_id, newest_report.new.document.type
            ).get_title(lang)

            result.append(
                "* {timestamp} "
                "([{diff_title}]({diff_url}) | [hist]({hist_url})) **·** "
                "({delta}) **·** "
                "[{doc_title}]({doc_url}) → "
                "*{modifications} modifications*".format(
                    timestamp=_format_timestamp(
                        newest_report.contrib.written_at, with_date
                    ),
                    doc_title=title if len(title) else "*Vide*",
                    doc_url=newest_report.new.document.get_url(lang),
                    hist_url=newest_report.new.document.get_history_url(
                        newest_report.contrib.lang
                    ),
                    diff_title="**new**" if not oldest_report.old else "diff",
                    diff_url=_get_diff_url(
                        bot,
                        newest_report.contrib.document,
                        lang,
                        oldest_report.new.previous_version_id,
                        newest_report.contrib.version_id,
                    ),
                    modifications=len(self.sub_reports),
                    delta=_format_delta(delta),
                )
            )

            for report in self.sub_reports:
                result.append(report.get_multi_report(lang, with_date))

        return "\n".join(result)


def build_legend(tests):
    """
    Legend of the markers, as a Markdown table: BBCode ([color=red]) and Markdown
    are not interpreted inside HTML blocks (<table>), only in Markdown tables.
    """

    def cell(text):
        return str(text).replace("|", "&#124;").replace("\n", " ") or " "

    lines = [
        "[details=Signification des icônes]\n",
        "| Test | A relire | Corrigé |",
        "|---|---|---|",
    ]
    for test in tests:
        lines.append(
            "| {} | {} | {} |".format(
                cell(test.name), cell(test.fail_marker), cell(test.success_marker)
            )
        )
    lines.append("\n[/details]")
    return "\n".join(lines)


def report_recent_changes(bot, days, lang, thread_url):

    newest_date = utils.today().replace(hour=0, minute=0, second=0, microsecond=0)
    oldest_date = newest_date - datetime.timedelta(days=days)

    tests = get_fixed_tests(lang)
    tests += get_re_tests(bot.forum.get_post(url=thread_url), lang)

    items = bot.get_modified_documents(
        lang=lang, oldest_date=oldest_date, newest_date=newest_date
    ).values()

    reports = []

    logging.info(f"Found {len(items)} contributions, processing...")

    for i, contributions in enumerate(items):
        logging.info("Build report {}/{}".format(i, len(items)))
        report = DocumentReport(bot, contributions, tests)
        if report.need_report:
            reports.append(report)

    if len(reports) != 0:
        messages = [
            "[Explications]({})\n".format(thread_url),
            build_legend(tests),
            "\n----\n",
        ]

        messages += [report.get_report(bot, lang, days > 1) for report in reports]

        logging.info(f"Reporting {len(reports)} reports:\n\n" + "\n".join(messages))

        bot.forum.post_message("\n".join(messages), thread_url)
    else:
        logging.info("Nothing to report")


def emoji(src, text):
    # width/height are explicit: the CSS class alone is not enough on the new forum
    # and the emoji images are 72px wide, which makes them huge
    return '<img src="{}" class="emoji" width="20" height="20" title="{}" alt="{}">'.format(
        src, text, text
    )


def convert_legacy_markup(text):
    """
    Convert the HTML markup used by the old forum for the markers
    (<font color="red"><strong>L#</strong></font>) to the BBCode/Markdown
    understood by the new one ([color=red]**L#**[/color]).
    """
    text = re.sub(
        r"""<font +color=["']?([#\w]+)["']? *>(.*?)</font>""",
        r"[color=\1]\2[/color]",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return re.sub(
        r"<(strong|b)>(.*?)</\1>", r"**\2**", text, flags=re.IGNORECASE | re.DOTALL
    )


def get_re_tests(configuration, lang):
    result = []

    test = None
    for line in configuration.raw.split("\n"):
        if line.startswith("#"):
            test = ReTest(line.lstrip("# "), lang)
            result.append(test)
        elif line.startswith("    ") and test:
            pattern = line[4:]
            if len(pattern.strip()) != 0:
                test.patterns.append(line[4:])
        else:
            parts = line.split(":", 1)

            if parts[0].strip() in ("* Erreur",):
                test.fail_marker = convert_legacy_markup(parts[1].strip())
            elif parts[0].strip() in ("* Corrigé",):
                test.success_marker = convert_legacy_markup(parts[1].strip())

    return filter(lambda t: len(t.patterns) != 0, result)


def get_fixed_tests(lang):
    return [
        HistoryTest(lang),
        LengthTest(lang),
        NewbieTest(),
        MainWaypointTest(),
        RouteTypeTest(),
        DistanceTest(),
        QualityTest(),
        TitleLevelTest(lang),
    ]


def get_document_tests(lang):
    """Returns a list of tests that can be run on a single document"""

    return [
        HistoryTest(lang),
        MainWaypointTest(),
        RouteTypeTest(),
    ]


class _BaseTest(object):
    def __init__(self, name, lang=None):
        self.name = name
        self.lang = lang

    def __call__(self, contrib, old_version, new_version):
        raise NotImplementedError()


class BaseVersionTest(_BaseTest):
    def __init__(self, name, lang=None):
        super(BaseVersionTest, self).__init__(name, lang)

    def __call__(self, contrib, old_version, new_version):
        return self.test_version(old_version), self.test_version(new_version)

    def test_version(self, version):
        if not version or not version.document:
            return True

        if "redirects_to" in version.document:
            return True

        return self.test_document(document=version.document)

    def test_document(self, document):
        raise NotImplementedError()


class BaseContributionTest(_BaseTest):
    def __init__(self, name, lang=None):
        super(BaseContributionTest, self).__init__(name, lang)

    def __call__(self, contrib, old_version, new_version):
        if not old_version or not new_version:
            return True, True

        if not old_version.document or not new_version.document:
            return True, True

        old_doc = old_version.document
        new_doc = new_version.document

        if "redirects_to" in old_doc or "redirects_to" in new_doc:
            return True, True

        return True, self.test_contribution(old_doc, new_doc)


class LengthTest(BaseContributionTest):
    def __init__(self, lang):
        super(LengthTest, self).__init__(name="Grosse suppression", lang=lang)

        self.fail_marker = emoji("/images/emoji/apple/rage.png?v=3", self.name)
        self.success_marker = ""

    def test_contribution(self, old_doc, new_doc):

        result = True

        old_locale_length = old_doc.get_locale(self.lang).get_length()
        new_locale_length = new_doc.get_locale(self.lang).get_length()

        if old_locale_length != 0 and new_locale_length / old_locale_length < 0.5:
            result = False

        return result


class NewbieTest(_BaseTest):
    def __init__(self):
        super(NewbieTest, self).__init__(name="Nouvel utilisateur")

        self.fail_marker = emoji("/images/emoji/apple/gift.png?v=3", self.name)
        self.success_marker = ""

    def __call__(self, contrib, old_version, new_version):
        if contrib.user.is_newbie():
            return True, False
        else:
            return True, True


class ReTest(BaseVersionTest):
    def __init__(self, name, lang):
        super(ReTest, self).__init__(name=name, lang=lang)
        self.patterns = []
        self.fail_marker = emoji("/images/emoji/apple/red_circle.png?v=3", self.name)
        self.success_marker = emoji(
            "/images/emoji/apple/white_check_mark.png?v=3", self.name + " corrigé"
        )

    def test_document(self, document):
        return not document.search(self.patterns, self.lang)


class HistoryTest(BaseVersionTest):
    activities_with_history = [
        "snow_ice_mixed",
        "mountain_climbing",
        "rock_climbing",
        "ice_climbing",
    ]

    def __init__(self, lang):
        super(HistoryTest, self).__init__(name="Champ historique", lang=lang)
        self.fail_marker = emoji("/images/emoji/apple/closed_book.png?v=3", self.name)
        self.success_marker = emoji(
            "/images/emoji/apple/green_book.png?v=3", self.name + " rempli"
        )

    def test_document(self, document):
        if document.type != "r":
            return True

        if (
            len(
                [
                    act
                    for act in document.activities
                    if act in self.activities_with_history
                ]
            )
            == 0
        ):
            return True

        locale = document.get_locale(self.lang)
        if locale and (not locale.route_history or len(locale.route_history) == 0):
            return False

        return True


class MainWaypointTest(BaseVersionTest):
    def __init__(self):
        super(MainWaypointTest, self).__init__(name="Point de passage principal")

        self.fail_marker = emoji(
            "https://forum.camptocamp.org/uploads/default/original/2X/f/f2c72706b83fd5bd21e110cb1b9758c763905023.png",
            self.name,
        )
        self.success_marker = emoji(
            "https://forum.camptocamp.org/uploads/default/original/2X/3/37abfd096a21bed932bea1d7150b9264abc12476.png",
            self.name + " corrigé",
        )

    def test_document(self, document):
        if document.type != "r":
            return True

        return document.main_waypoint_id is not None


class RouteTypeTest(BaseVersionTest):
    def __init__(self):
        super(RouteTypeTest, self).__init__(name="Type de voie renseigné")
        self.fail_marker = emoji("/images/emoji/apple/red_circle.png?v=3", self.name)
        self.success_marker = emoji(
            "/images/emoji/apple/white_check_mark.png?v=3", self.name + " corrigé"
        )

    def test_document(self, document):

        if document.type != "r" or "rock_climbing" not in document.activities:
            return True

        climbing_outdoor_type = document.climbing_outdoor_type
        return climbing_outdoor_type is not None and len(climbing_outdoor_type) != 0


class DistanceTest(BaseContributionTest):
    def __init__(self):
        super(DistanceTest, self).__init__(name="Gros déplacement géographique")
        self.fail_marker = emoji(
            "/uploads/default/original/2X/0/0178043b1b70e669946f609571bd4b8f7d18e820.png",
            self.name,
        )
        self.success_marker = ""

    def test_contribution(self, old_doc, new_doc):
        distance = utils.compute_distance(old_doc, new_doc)
        return distance is None or distance < 500


class QualityTest(BaseContributionTest):
    """
    Report when quality field changes
    """

    def __init__(self):
        super(QualityTest, self).__init__(name="Changement du champ qualité")
        self.fail_marker = "🧹"
        self.success_marker = ""

    def test_contribution(self, old_doc, new_doc):
        return old_doc.quality == new_doc.quality


class TitleLevelTest(BaseVersionTest):
    """A text with titles must not use level 1 (#) and needs a level 2 (##)"""

    title = re.compile(r"^(#+)[ 	]", re.MULTILINE)

    def __init__(self, lang):
        super(TitleLevelTest, self).__init__(name="Niveau des titres", lang=lang)
        self.fail_marker = emoji("/images/emoji/apple/hash.png?v=3", self.name)
        self.success_marker = emoji(
            "/images/emoji/apple/white_check_mark.png?v=3", self.name + " corrigé"
        )

    def test_document(self, document):
        locale = document.get_locale(self.lang)

        if not locale:
            return True

        for field in locale.get_locale_fields():
            if field in locale and locale[field]:
                levels = {len(m) for m in self.title.findall(locale[field])}

                if levels and (1 in levels or 2 not in levels):
                    return False

        return True
