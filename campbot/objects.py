# coding: utf-8

from __future__ import print_function, unicode_literals, division

import re
from .differ import get_diff_report


def get_constructor(document_type):
    return {"u": WikiUser,
            "a": Area,
            "w": Waypoint,
            "o": Outing,
            "i": Image,
            "m": Map,
            "x": Xreport,
            "c": Article,
            "b": Book,
            "r": Route}[document_type]


class BotObject(dict):
    def __init__(self, campbot, data):
        super(BotObject, self).__init__(data)
        self._campbot = campbot

        # we must define __setattr__ after _campbot, otherwise it will be stored in dict
        self.__setattr__ = self.__setitem__

    # make instance.key equivalent to instance["key"]
    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError

        return self[item]

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            super().__setattr__(key, value)

    def _convert_list(self, name, constructor):
        if name in self:
            self[name] = [constructor(self._campbot, data) for data in self[name]]

    def _convert_dict(self, name, constructor):
        if name in self:
            self[name] = {key: constructor(self._campbot, self[name][key]) for key in self[name]}


class Version(BotObject):
    def __init__(self, campbot, data):
        super(Version, self).__init__(campbot, data)
        self['document'] = get_constructor(self['document']['type'])(campbot, self['document'])

    def get_diff_url(self, lang):
        constructor = get_constructor(document_type=self.document.type)

        if not self.previous_version_id:
            return self.document.get_url(lang)

        return "{}/{}/diff/{}/{}/{}/{}".format(
            self._campbot.wiki.ui_url,
            constructor.url_path,
            self.document.document_id,
            lang,
            self.previous_version_id,
            self.version["version_id"]
        )

    def get_locale_length(self, lang):
        locale = self.document.get_locale(lang)

        return locale.get_length() if locale else 0


class Contribution(BotObject):
    def __init__(self, campbot, data):
        super(Contribution, self).__init__(campbot, data)
        self['document'] = get_constructor(self['document']['type'])(campbot, self['document'])
        self['user'] = ShortWikiUser(campbot, self['user'])

    def get_full_document(self):
        return self._campbot.wiki.get_wiki_object(self.document["document_id"],
                                                  document_type=self.document["type"])


class Locale(BotObject):
    def get_title(self):
        if "title_prefix" in self:
            return "{} : {}".format(self.title_prefix, self.title)
        else:
            return self.title

    def get_locale_fields(self):
        return ("description", "gear", "remarks", "route_history",
                "summary", "access", "access_period", "title",
                "external_resources", "other_comments", "slope",
                "slackline_anchor1", "slackline_anchor2")

    def get_length(self):
        result = 0
        for field in self.get_locale_fields():
            if field in self and self[field]:
                result += len(self[field])

        return result


class WikiObject(BotObject):
    url_path = None

    def __init__(self, campbot, data):
        super(WikiObject, self).__init__(campbot, data)
        self._convert_list("locales", Locale)
        self._data = data

    def get_url(self, lang=None):
        return "{}/{}/{}{}".format(self._campbot.wiki.ui_url,
                                   self.url_path,
                                   self.document_id,
                                   "" if lang is None else "/" + lang)

    def get_history_url(self, lang):
        return "{}/{}/history/{}/{}".format(self._campbot.wiki.ui_url,
                                            self.url_path,
                                            self.document_id,
                                            lang)

    def get_title(self, lang):
        locale = self.get_locale(lang)
        return locale.get_title() if locale else ""

    def get_locale(self, lang):
        if "locales" not in self:
            return None

        for locale in self.locales:
            if locale.lang == lang:
                return locale

    def search(self, patterns, lang):

        locale = self.get_locale(lang)

        for field in locale.get_locale_fields():
            if field in locale and locale[field]:
                for pattern in patterns:
                    if re.search(pattern, locale[field]):
                        return True
        return False

    def print_diff(self):
        report = get_diff_report(self._data, self)

        for l in report:
            print(l)

    def save(self, message, ask_before_saving=True):
        self.print_diff()

        if ask_before_saving:
            if input("Save {} : {}, y/[n] ?\n".format(self.get_url(), message)) != "y":
                return None
        else:
            print("Saving {} : {}".format(self.get_url(), message))

        payload = {"document": self, "message": message}
        return self._campbot.wiki.put("/{}/{}".format(self.url_path, self.document_id), payload)

    def is_valid(self):
        return self.get_invalidity_reason() is None

    def is_personal(self):
        return False

    def get_invalidity_reason(self):
        return None


class ShortWikiUser(BotObject):
    def get_contributions_url(self):
        return "{}/whatsnew#u={}".format(self._campbot.wiki.ui_url, self.user_id)

    def is_newbie(self):
        contribs = self._campbot.wiki.get("/documents/changes?limit=50&u={}".format(self.user_id))
        return len(contribs["feed"]) < 50

    def get_wiki_user(self):
        return self._campbot.wiki.get_user(user_id=self.user_id)


class WikiUser(WikiObject):
    url_path = "profiles"

    def get_contributions(self, oldest_date=None, newest_date=None):
        return self._campbot.wiki.get_contributions(user_id=self.document_id,
                                                    oldest_date=oldest_date,
                                                    newest_date=newest_date)

    def get_last_contribution(self, oldest_date=None, newest_date=None):
        for contribution in self.get_contributions(oldest_date=oldest_date,
                                                   newest_date=newest_date):
            return contribution

        return None

    def is_personal(self):
        return True


class Route(WikiObject):
    url_path = "routes"


class Article(WikiObject):
    url_path = "articles"

    def is_personal(self):
        return self.article_type == "personal"


class Image(WikiObject):
    url_path = "images"

    def is_personal(self):
        return self.image_type in ("personal", "copyright")


class Book(WikiObject):
    url_path = "books"


class Xreport(WikiObject):
    url_path = "xreports"

    def is_personal(self):
        return True


class Waypoint(WikiObject):
    url_path = "waypoints"

    def get_invalidity_reason(self):
        if self.waypoint_type in ("hut", "gite") and self.custodianship is None:
            return "custodianship is missing"

        if self.elevation is None and self.waypoint_type not in (
            "climbing_indoor",):
            return "elevation is missing"

        return None


class Area(WikiObject):
    url_path = "areas"


class Map(WikiObject):
    url_path = "maps"


class Outing(WikiObject):
    url_path = "outings"

    def is_personal(self):
        return True


class ForumUser(BotObject):
    def get_wiki_user(self):
        return self._campbot.wiki.get_user(forum_name=self.username)


class Post(BotObject):
    def __init__(self, campbot, data):
        super(Post, self).__init__(campbot, data)
        self._convert_dict("polls", Poll)


class Poll(BotObject):
    def __init__(self, campbot, data):
        super(Poll, self).__init__(campbot, data)
        self._convert_list("options", PollOption)


class PollOption(BotObject):
    def get_voters(self, post_id, poll_name):
        url = "/polls/voters.json?post_id={}&poll_name={}&option_id={}&offset={}"
        offset = 0
        while True:
            data = self._campbot.forum.get(
                url.format(post_id, poll_name, self.id, offset))[poll_name]

            if self.id not in data or len(data[self.id]) == 0:
                raise StopIteration
            for voter in data[self.id]:
                yield ForumUser(self._campbot, voter)

            offset += 1
