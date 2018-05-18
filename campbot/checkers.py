# coding: utf-8

from __future__ import unicode_literals, print_function, division

from dateutil import parser


def check_recent_changes(bot, ask_before_saving):
    check_message_url = "https://forum.camptocamp.org/t/topoguide-verifications-automatiques/201480"
    lang = "fr"

    oldest_date = bot.forum.get_last_message_timestamp(
        check_message_url,
        "rabot"
    )

    bot.fix_recent_changes(oldest_date, lang, ask_before_saving)

    tests = get_fixed_tests(lang)
    tests += get_re_tests(bot.forum.get_post(url=check_message_url), lang)

    messages = [
        "[Explications]({})\n".format(check_message_url),
        "[details=Signification des icônes]\n<table>",
        "<tr><th>Test</th><th>A relire</th><th>Corrigé</th></tr>",
    ]

    for test in tests:
        messages.append("<tr>")
        messages.append("<th>{}</th>".format(test.name))
        messages.append("<td>{}</td>".format(test.fail_marker))
        messages.append("<td>{}</td>".format(test.success_marker))
        messages.append("</tr>")

    messages.append("</table>\n[/details]\n\n----\n\n")

    items = bot.get_modified_documents(lang=lang, oldest_date=oldest_date)

    for contribs in items.values():
        need_report = False
        report = []

        if len(contribs) != 1:
            report.append("* {} modifications ".format(len(contribs), ))

        for contrib in contribs:
            print(contrib.written_at, "get doc")
            new = bot.wiki.get_wiki_object_version(contrib.document.document_id,
                                                   contrib.document.type,
                                                   contrib.lang,
                                                   contrib.version_id)

            old = bot.wiki.get_wiki_object_version(contrib.document.document_id,
                                                   contrib.document.type,
                                                   contrib.lang,
                                                   new.previous_version_id)

            emojis = []

            for test in tests:
                old_is_ok, new_is_ok = test(contrib, old, new)

                if old_is_ok and not new_is_ok:
                    emojis.append(test.fail_marker)
                    need_report = True
                elif not old_is_ok and new_is_ok:
                    emojis.append(test.success_marker)

            delta = new.get_locale_length(contrib.lang) if new else 0
            delta -= old.get_locale_length(contrib.lang) if old else 0

            if delta < 0:
                delta = "<del>{:+d}</del>".format(delta)
            elif delta > 0:
                delta = "<ins>{:+d}</ins>".format(delta)
            else:
                delta = "**=**"

            title = new.document.get_title(lang)

            report.append(
                "{prefix}* {timestamp} {emojis} [{doc_title}]({doc_url}) "
                "([{diff_title}]({diff_url}) | [hist]({hist_url})) "
                "**·** ({delta}) **·** [{username}]({user_contrib_url})"
                " →‎ *{comment}*".format(
                    prefix="" if len(contribs) == 1 else "  ",
                    timestamp=parser.parse(contrib.written_at).strftime("%H:%M"),
                    emojis="".join(emojis),
                    doc_title=title if len(title) else "*Vide*",
                    doc_url=new.document.get_url(lang),
                    diff_title="diff" if new.previous_version_id else "**new**",
                    diff_url=new.get_diff_url(lang),
                    hist_url=new.document.get_history_url(contrib.lang),
                    delta=delta,
                    username=contrib.user.name,
                    user_contrib_url=contrib.user.get_contributions_url(),
                    comment=contrib.comment if len(contrib.comment) else "&nbsp;"
                )
            )

        if need_report:
            messages += report

    for m in messages:
        print(m)

    if len(messages) != 0:
        bot.forum.post_message("\n".join(messages), check_message_url)


def emoji(src, text):
    return '<img src="{}" class="emoji" title="{}" alt="{}">'.format(src, text, text)


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
                test.fail_marker = parts[1].strip()
            elif parts[0].strip() in ("* Corrigé",):
                test.success_marker = parts[1].strip()

    return filter(lambda t: len(t.patterns) != 0, result)


def get_fixed_tests(lang):
    return [HistoryTest(lang), LengthTest(lang), NewbieTest(), MainWaypointTest(), RouteTypeTest()]


class LengthTest(object):
    def __init__(self, lang):
        self.name = "Grosse suppression"
        self.lang = lang

        self.fail_marker = emoji("/images/emoji/apple/rage.png?v=3", self.name)
        self.success_marker = ""

    def __call__(self, contrib, old_version, new_version):
        old_doc = old_version.document if old_version else None
        new_doc = new_version.document if new_version else None

        if not old_doc or "redirects_to" in old_doc:
            return True, True

        if not new_doc or "redirects_to" in new_doc:
            return True, True

        result = True

        old_locale_length = old_doc.get_locale(self.lang).get_length()
        new_locale_length = new_doc.get_locale(self.lang).get_length()

        if old_locale_length != 0 and new_locale_length / old_locale_length < 0.5:
            result = False

        return True, result


class NewbieTest(object):
    def __init__(self):
        self.name = "Nouvel utilisateur"

        self.fail_marker = emoji("/images/emoji/apple/gift.png?v=3", self.name)
        self.success_marker = ""

    def __call__(self, contrib, old_version, new_version):
        if contrib.user.is_newbie():
            return True, False
        else:
            return False, False


class ReTest(object):
    def __init__(self, name, lang):
        self.name = name
        self.lang = lang
        self.patterns = []
        self.fail_marker = emoji("/images/emoji/apple/red_circle.png?v=3", self.name)
        self.success_marker = emoji("/images/emoji/apple/white_check_mark.png?v=3",
                                    self.name + " corrigé")

    def __call__(self, contrib, old_version, new_version):
        old_doc = old_version.document if old_version else None
        new_doc = new_version.document if new_version else None

        def test(doc):
            if not doc or "redirects_to" in doc:
                return True

            return not doc.search(self.patterns, self.lang)

        return test(old_doc), test(new_doc)


class HistoryTest(object):
    activities_with_history = ["snow_ice_mixed", "mountain_climbing", "rock_climbing", "ice_climbing"]

    def __init__(self, lang):
        self.name = "Champ historique"
        self.lang = lang
        self.fail_marker = emoji("/images/emoji/apple/closed_book.png?v=3", self.name)
        self.success_marker = emoji("/images/emoji/apple/green_book.png?v=3", self.name + " rempli")

    def __call__(self, contrib, old_version, new_version):
        old_doc = old_version.document if old_version else None
        new_doc = new_version.document if new_version else None

        def test(doc):
            if not doc or "redirects_to" in doc or doc.type != "r":
                return True

            if len([act for act in doc.activities if act in self.activities_with_history]) == 0:
                return True

            locale = doc.get_locale(self.lang)
            if locale and (not locale.route_history or len(locale.route_history) == 0):
                return False

            return True

        return test(old_doc), test(new_doc)


class MainWaypointTest(object):
    def __init__(self):
        self.name = "Main waypoint"
        self.fail_marker = emoji("https://www.openstreetmap.org/assets/marker-red.png", self.name)
        self.success_marker = emoji("https://www.openstreetmap.org/assets/marker-green.png", self.name + " corrigé")

    def __call__(self, contrib, old_version, new_version):
        if new_version.document.type != "r":
            return True, True

        def test(version):
            if not version:
                return True

            if "redirects_to" in version.document:
                return True

            return version.document.main_waypoint_id is not None

        return test(old_version), test(new_version)


class RouteTypeTest(object):
    def __init__(self):
        self.name = "Type de voie renseigné"
        self.fail_marker = emoji("/images/emoji/apple/red_circle.png?v=3", self.name)
        self.success_marker = emoji("/images/emoji/apple/white_check_mark.png?v=3",
                                    self.name + " corrigé")

    def __call__(self, contrib, old_version, new_version):
        def test(version):
            if not version:
                return True

            if "redirects_to" in version.document:
                return True

            if version.document.type != "r" or "rock_climbing" not in version.document.activities:
                return True

            climbing_outdoor_type = version.document.climbing_outdoor_type
            return climbing_outdoor_type is not None and len(climbing_outdoor_type) != 0

        return test(old_version), test(new_version)
