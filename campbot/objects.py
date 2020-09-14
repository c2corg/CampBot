# coding: utf-8

"""

This module contains all data objects getted from forum and wiki API. These API provides JSON data, and this module enhances data model by mirroring data attributes to data model. Here is an exemple : 

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    waypoint = bot.wiki.get_waypoint(107702)
    
    # this two lines are perfectly equivalents
    elevation = waypoint["elevation"]  # standard way to access data
    elevation = waypoint.elevation  # and sexier way.
    
    # set values is possible
    waypoint.elevation = 1000  
    assert waypoint["elevation"] == 1000  # it's true!
    
We try to use the second way every times it's possible in this documentation.
"""

from __future__ import print_function, unicode_literals, division

import re
from .differ import get_diff_report


def _input(message):  # pragma: no cover
    try:  # py 2
        return raw_input(message)
    except NameError:  # py 3
        return input(message)


def get_constructor(document_type):
    return {
        "u": WikiUser,
        "a": Area,
        "w": Waypoint,
        "o": Outing,
        "i": Image,
        "m": Map,
        "x": Xreport,
        "c": Article,
        "b": Book,
        "r": Route,
    }[document_type]


class BotObject(dict):
    """
    Base class for all data object
    """

    def __init__(self, campbot, data):
        super(BotObject, self).__init__(data)
        self._campbot = campbot

    # make instance.key equivalent to instance["key"]
    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(
                "Object {} has not attribute {}".format(self.__class__.__name__, item)
            )

        if item not in self:  # pragma: no cover
            print("666777", self)
            raise AttributeError(
                "Object {} has not attribute {}".format(self.__class__.__name__, item)
            )

        return self[item]

    def __setattr__(self, key, value):
        if key in self:
            self[key] = value
        else:
            super(BotObject, self).__setattr__(key, value)

    def _convert_list(self, name, constructor):
        if name in self:
            self[name] = [constructor(self._campbot, data) for data in self[name]]

    # def _convert_dict(self, name, constructor):
    #     if name in self:
    #         self[name] = {
    #             key: constructor(self._campbot, self[name][key]) for key in self[name]
    #         }


class Version(BotObject):
    """
    A historical version of one wiki document.
    """

    def __init__(self, campbot, data):
        super(Version, self).__init__(campbot, data)
        if self["document"]:
            self["document"] = get_constructor(self["document"]["type"])(
                campbot, self["document"]
            )
        else:
            self["document"] = None

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
            self.version["version_id"],
        )

    def get_locale_length(self, lang):
        locale = self.document.get_locale(lang)

        return locale.get_length() if locale else 0


class Contribution(BotObject):
    def __init__(self, campbot, data):
        super(Contribution, self).__init__(campbot, data)
        self["document"] = get_constructor(self["document"]["type"])(
            campbot, self["document"]
        )
        self["user"] = ShortWikiUser(campbot, self["user"])

    def get_full_document(self):
        return self._campbot.wiki.get_wiki_object(
            self.document["document_id"], document_type=self.document["type"]
        )


class Locale(BotObject):
    """
    Locale is a set of field, given a lang.
    """

    def get_title(self):
        """
        Get the title, with prefix if it exists.
        
        :return: String, pretty title
        """

        if "title_prefix" in self:
            return "{} : {}".format(self.title_prefix, self.title)
        else:
            return self.title

    def get_locale_fields(self):
        return (
            "description",
            "gear",
            "remarks",
            "route_history",
            "summary",
            "access",
            "access_period",
            "title",
            "external_resources",
            "other_comments",
            "slope",
            "slackline_anchor1",
            "slackline_anchor2",
        )

    def get_length(self):
        """
        Get text length
        
        :return: Integer, number of characters
        """

        result = 0
        for field in self.get_locale_fields():
            if field in self and self[field]:
                result += len(self[field])

        return result


class WikiObject(BotObject):
    """
    Base object for all wiki documents
    """

    url_path = None

    def __init__(self, campbot, data):
        super(WikiObject, self).__init__(campbot, data)

        if "associations" in self and self["associations"] is not None:
            self["associations"] = BotObject(campbot=campbot, data=self["associations"])
            self.associations._convert_list("images", Image)

        self._convert_list("locales", Locale)
        self._data = data

    def get_url(self, lang=None):
        """
        :return: camptocamp.org URL.  
        """

        return "{}/{}/{}{}".format(
            self._campbot.wiki.ui_url,
            self.url_path,
            self.document_id,
            "" if lang is None else "/" + lang,
        )

    def get_history_url(self, lang):
        """
        
        :return: camptocamp.org version list URL
        """

        return "{}/{}/history/{}/{}".format(
            self._campbot.wiki.ui_url, self.url_path, self.document_id, lang
        )

    def get_title(self, lang):
        locale = self.get_locale(lang)
        return locale.get_title() if locale else ""

    def get_locale(self, lang):
        """
        :param lang: fr, en, de ...
        
        :return: String, or None if locale does not exists in this lang  
        """

        if "locales" not in self:
            return None

        for locale in self.locales:
            if locale.lang == lang:
                return locale

    def search(self, patterns, lang):
        """
        Search a pattern (regular expression)
        
        :param lang: fr, de, en...
        
        :return: True if pattern is found, False otherwise
        """

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

    def _build_payload(self, message):
        return {"document": self, "message": message}

    def save(self, message, ask_before_saving=True):
        """
        Save object to camptocamp.org. Bot must be authentified.
        
        :param message: Modification comment
        :param ask_before_saving: Boolean, ask user before saing document
        
        :return: raw request response, useless.
        """

        self.print_diff()

        if ask_before_saving:
            if _input("Save {} : {}, y/[n] ?\n".format(self.get_url(), message)) != "y":
                return None
        else:
            print("Saving {} : {}".format(self.get_url(), message))

        return self._campbot.wiki.put(
            "/{}/{}".format(self.url_path, self.document_id),
            self._build_payload(message),
        )

    def is_valid(self):
        """
        :return: True if document can be saved
        """

        return self.get_invalidity_reason() is None

    def is_personal(self):
        return False

    def get_invalidity_reason(self):
        return None


class ShortWikiUser(BotObject):
    def get_contributions_url(self):
        return "{}/whatsnew#u={}".format(self._campbot.wiki.ui_url, self.user_id)

    def is_newbie(self):
        contribs = self._campbot.wiki.get(
            "/documents/changes?limit=50&u={}".format(self.user_id)
        )
        return len(contribs["feed"]) < 50

    def get_wiki_user(self):
        return self._campbot.wiki.get_user(user_id=self.user_id)


class WikiUser(WikiObject):
    url_path = "profiles"

    def get_contributions(self, oldest_date=None, newest_date=None):
        return self._campbot.wiki.get_contributions(
            user_id=self.document_id, oldest_date=oldest_date, newest_date=newest_date
        )

    def get_last_contribution(self, oldest_date=None, newest_date=None):
        for contribution in self.get_contributions(
            oldest_date=oldest_date, newest_date=newest_date
        ):
            return contribution

        return None

    def is_personal(self):
        return True


class Route(WikiObject):
    """Route object : https://www.camptocamp.org/routes"""

    url_path = "routes"


class Article(WikiObject):
    """Article object : https://www.camptocamp.org/articles"""

    url_path = "articles"

    def is_personal(self):
        return self.article_type == "personal"


class Image(WikiObject):
    """Image object : https://www.camptocamp.org/images"""

    url_path = "images"

    def is_personal(self):
        return self.image_type in ("personal", "copyright")


class Book(WikiObject):
    """Book object : https://www.camptocamp.org/books"""

    url_path = "books"


class Xreport(WikiObject):
    """Xreport object : https://www.camptocamp.org/xreports"""

    url_path = "xreports"

    def is_personal(self):
        return True


class Waypoint(WikiObject):
    """Waypoint object : https://www.camptocamp.org/waypoints"""

    url_path = "waypoints"

    def get_invalidity_reason(self):
        if self.waypoint_type in ("hut", "gite") and self.custodianship is None:
            return "custodianship is missing"

        if self.elevation is None and self.waypoint_type not in ("climbing_indoor",):
            return "elevation is missing"

        return None


class Area(WikiObject):
    """Area object : https://www.camptocamp.org/areas"""

    url_path = "areas"

    def _build_payload(self, message):
        payload = super(Area, self)._build_payload(message)

        #  Geometry info must not be present in payload, otherwise, save actions fails
        del payload["document"]["geometry"]

        return payload


class Map(WikiObject):
    """Map object : https://www.camptocamp.org/maps"""

    url_path = "maps"


class Outing(WikiObject):
    """Outings object : https://www.camptocamp.org/outings"""

    url_path = "outings"

    def is_personal(self):
        return True


class ForumUser(BotObject):
    pass


class Post(BotObject):
    def __init__(self, campbot, data):
        super(Post, self).__init__(campbot, data)
        self._convert_list("polls", Poll)


class Poll(BotObject):
    def __init__(self, campbot, data):
        super(Poll, self).__init__(campbot, data)
