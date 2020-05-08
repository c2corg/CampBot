# coding: utf-8

from __future__ import print_function

import sqlite3
import re

from campbot import CampBot
from requests.exceptions import HTTPError

from copy import deepcopy
from dateutil.parser import parse as parse_datetime
from time import time

try:
    _ = basestring  # py2
except NameError:
    basestring = (str,)  # py3

_default_db_name = "camptocamp.db"


def prepare_for_insertion(doc):
    result = deepcopy(doc)

    result["creator"] = result.pop("creator", {}).get("user_id", None)
    if isinstance(result.get("author", None), dict):
        result["author"] = (result.pop("author", {}) or {}).get("user_id", None)

    if "date_time" in result and result["date_time"] is not None:
        result["date_time"] = int(parse_datetime(result["date_time"]).timestamp())

    result.pop("available_langs", None)

    result["associations"] = result["associations"] or {}
    result["associations"].pop("recent_outings", None)
    result["associations"].pop("all_routes", None)
    result["associations"]["maps"] = result.pop("maps", [])
    result["associations"]["areas"] = result.pop("areas", [])
    associations = []
    for items in result["associations"].values():
        for item in items:
            associations.append(item["document_id"])

    result["associations"] = associations

    return result


class Dump(object):
    def __init__(self, db_name=None):
        super(Dump, self).__init__()

        self._conn = sqlite3.connect(db_name or _default_db_name)

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS document ("
            " document_id INTEGER PRIMARY KEY,"
            " type CHAR(1),"
            " version_id INTEGER NOT NULL,"
            " filename TEXT,"
            " geometry_geom TEXT,"
            " geometry_geom_detail TEXT,"
            " geometry_version INTEGER"
            ") WITHOUT ROWID;"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS locale ("
            " document_id INT,"
            " lang CHAR(2),"
            " field VARCHAR,"
            " value TEXT"
            ");"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS contribution ("
            " version_id INTEGER PRIMARY KEY DESC,"
            " document_id INTEGER,"
            " user_id INTEGER,"
            " type CHAR(1),"
            " written_at CHAR(32)"
            ") WITHOUT ROWID;"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS string_property ("
            " document_id INTEGER,"
            " field INTEGER,"
            " value INTEGER"
            ");"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS integer_property ("
            " document_id INTEGER,"
            " field INTEGER,"
            " value INTEGER"
            ");"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS real_property ("
            " document_id INTEGER,"
            " field INTEGER,"
            " value REAL"
            ");"
        )

        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS string ("
            " string_id INTEGER PRIMARY KEY,"
            " value TEXT"
            ");"
        )

        self._conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS IX_document_document_id "
            " ON document(document_id);"
        )

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS IX_locale_document_id "
            " ON locale(document_id);"
        )

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS IX_contribution_document_id "
            " ON contribution(document_id);"
        )

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS IX_real_property_document_id "
            " ON real_property(document_id);"
        )

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS IX_integer_property_document_id "
            " ON integer_property(document_id);"
        )

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS IX_string_property_document_id "
            " ON string_property(document_id);"
        )

        def regexp(y, x, search=re.search):
            return 1 if search(y, str(x)) else 0

        self._conn.create_function("regexp", 2, regexp)

        self.string_ids = {}

        for row in self._conn.execute("SELECT string_id, value FROM string"):
            self.string_ids[row[1]] = row[0]

    def get_string_id(self, string, cur):
        if string not in self.string_ids:
            cur.execute("INSERT INTO string(value) VALUES (?)", (string,))
            self.string_ids[string] = cur.lastrowid

        return self.string_ids[string]

    def _insert_prop(self, doc, key, value, cur):

        if value is None:
            return

        if isinstance(value, list):
            for sub_value in value:
                self._insert_prop(doc, key, sub_value, cur)

        elif isinstance(value, dict):
            for sub_key in value:
                self._insert_prop(doc, key + "." + sub_key, value[sub_key], cur)

        else:
            key_id = self.get_string_id(key, cur)

            if isinstance(value, (bool, int)):
                cur.execute(
                    "INSERT INTO integer_property"
                    "(document_id,field,value)"
                    "VALUES (?,?,?)",
                    (doc.document_id, key_id, value),
                )

            elif isinstance(value, float):
                cur.execute(
                    "INSERT INTO real_property"
                    "(document_id,field,value)"
                    "VALUES (?,?,?)",
                    (doc.document_id, key_id, value),
                )

            elif isinstance(value, basestring):
                string_id = self.get_string_id(value, cur)

                cur.execute(
                    "INSERT INTO string_property"
                    "(document_id,field,value)"
                    "VALUES (?,?,?)",
                    (doc.document_id, key_id, string_id),
                )
            else:
                raise NotImplementedError(key, value)

    def delete(self, document_id):
        cur = self._conn.cursor()
        self._delete(document_id, cur)
        self._conn.commit()

    def _delete(self, document_id, cur):

        cur.execute("DELETE FROM document WHERE document_id=?", (document_id,))
        cur.execute("DELETE FROM locale WHERE document_id=?", (document_id,))
        cur.execute("DELETE FROM string_property WHERE document_id=?", (document_id,))
        cur.execute("DELETE FROM integer_property WHERE document_id=?", (document_id,))
        cur.execute("DELETE FROM real_property WHERE document_id=?", (document_id,))

    def insert(self, cur, base_doc=None, version_id=0, contrib=None):

        if not base_doc:
            base_doc = contrib.get_full_document()
            version_id = contrib.version_id

        self._delete(contrib.document.document_id, cur)

        if "redirects_to" in base_doc:
            return

        doc = prepare_for_insertion(base_doc)
        geometry = doc.pop("geometry", None) or {}

        props = (
            doc.document_id,
            doc.type,
            version_id,
            geometry.pop("version", None),
            geometry.pop("geom_detail", None),
            geometry.pop("geom", None),
            doc.pop("filename", None),
        )

        assert len(geometry) == 0

        cur.execute(
            "INSERT INTO document"
            "(document_id, type, version_id,"
            "geometry_version,geometry_geom_detail,geometry_geom,"
            "filename)"
            "VALUES (?,?,?,?,?,?,?)",
            props,
        )

        for key in doc:
            value = doc[key]

            if key == "locales":
                for locale in value:

                    lang = locale.pop("lang")

                    for field in locale:
                        value = locale[field]
                        if (
                            isinstance(value, str)
                            and len(value.strip()) != 0
                            and field not in ("version", "topic_id")
                        ):
                            field_id = self.get_string_id(field, cur)
                            cur.execute(
                                "INSERT INTO locale"
                                "(document_id,lang,field,value)"
                                "VALUES (?,?,?,?)",
                                (doc.document_id, lang, field_id, value),
                            )
            else:
                self._insert_prop(doc, key, value, cur)

    def select(self, document_id):
        sql = "SELECT * FROM document WHERE document_id=?;"

        cur = self._conn.cursor()
        cur.execute(sql, (document_id,))

        result = cur.fetchone()

        self._conn.commit()
        cur.close()

        return result

    def get_highest_version_id(self, table="document"):
        sql = "SELECT version_id from {} ORDER BY version_id DESC LIMIT 1".format(table)

        cur = self._conn.cursor()
        cur.execute(sql)

        result = cur.fetchone()

        self._conn.commit()
        cur.close()

        return result[0] if result else 0

    def complete_contributions(self):
        bot = CampBot(min_delay=0.01)

        highest_version_id = self.get_highest_version_id("contribution")

        cur = self._conn.cursor()

        for i, contrib in enumerate(
            bot.wiki.get_contributions(oldest_date="1990-12-25")
        ):
            if highest_version_id >= contrib.version_id:
                break

            print(contrib.written_at, contrib.version_id, contrib.user.username)

            doc = contrib.document
            try:
                cur.execute(
                    "INSERT INTO contribution"
                    "(document_id, type, version_id, user_id, written_at)"
                    "VALUES (?,?,?,?,?)",
                    (
                        doc.document_id,
                        doc.type,
                        contrib.version_id,
                        contrib.user.user_id,
                        contrib.written_at,
                    ),
                )
            except sqlite3.IntegrityError:
                pass

        self._conn.commit()

    def complete(self):

        bot = CampBot(min_delay=0.01)

        still_done = []
        highest_version_id = self.get_highest_version_id()

        cur = self._conn.cursor()

        for i, contrib in enumerate(
            bot.wiki.get_contributions(oldest_date="2018-01-24")
        ):
            if highest_version_id >= contrib.version_id:
                break

            key = (contrib.document.document_id, contrib.document.type)
            if key not in still_done:
                still_done.append(key)
                doc = contrib.get_full_document()

                self.insert(
                    cur=cur,
                    contrib=contrib,
                    version_id=contrib.version_id,
                    base_doc=doc,
                )
                print(i, contrib.written_at, key, "inserted")

        self._conn.commit()

        self.complete_contributions()

    def sql_file(self, filename):
        with open(filename) as f:
            sql = " ".join(f.readlines())

        return self._conn.execute(sql)

    def search(self, pattern, lang=None):
        sql = (
            "SELECT document.document_id, document.type, locale.lang, string.value, title.value, locale.value "
            "FROM locale "
            "LEFT JOIN document ON document.document_id=locale.document_id "
            "LEFT JOIN string ON string.string_id=locale.field "
            "LEFT JOIN locale as title ON document.document_id=title.document_id "
            "   AND title.lang=locale.lang "
            "   AND title.field=29 "
            "WHERE locale.value REGEXP ? "
            "AND string.value!='title' AND string.value!='title_prefix'"
        )

        if lang is not None:
            sql += " AND locale.lang=?"
            args = (pattern, lang)
        else:
            args = (pattern,)

        c = self._conn.cursor()
        c.execute(sql, args)
        return c.fetchall()

    def get_all_ids(self):

        sql = "SELECT document_id, type FROM document"

        cur = self._conn.cursor()
        cur.execute(sql)

        result = cur.fetchall()

        self._conn.commit()
        cur.close()

        return result

    def get_all_version_ids(self):

        sql = "SELECT version_id FROM contribution"

        cur = self._conn.execute(sql)
        result = cur.fetchall()

        return [r[0] for r in result]

    def re_update(self):
        from campbot import CampBot

        # c = self._conn.execute("SELECT document.document_id, document.type FROM document "
        #                        "LEFT OUTER JOIN string_property "
        #                        "    ON string_property.document_id = document.document_id "
        #                        "WHERE field IS NULL")

        c = self._conn.execute(
            "SELECT locale.document_id, document.type FROM locale "
            "LEFT JOIN document on document.document_id=locale.document_id "
            "WHERE field='blob'"
        )

        result = c.fetchall()

        bot = CampBot(min_delay=0.01)
        cur = None

        for i, (document_id, typ) in enumerate(result):
            if i % 50 == 0:
                self._conn.commit()
                cur = self._conn.cursor()

            t = time()
            try:
                doc = bot.wiki.get_wiki_object(item_id=document_id, document_type=typ)
                get_time = int((time() - t) * 1000)
                doc["document_id"] = document_id  # for redirects...
            except HTTPError as e:
                if e.response.status_code == 404:
                    print(document_id, "is deleted")
                    self._delete(document_id, cur)
                else:
                    raise
            else:
                t = time()
                self.insert(cur=cur, base_doc=doc)
                print(
                    "{}/{}".format(i, len(result)),
                    document_id,
                    typ,
                    get_time,
                    int((time() - t) * 1000),
                )

        self._conn.commit()


def get_document_types():
    return {doc_id: typ for doc_id, typ in Dump().get_all_ids()}


def _search(pattern, lang=None):
    from campbot.objects import get_constructor

    dump = Dump()

    with open("ids.txt", "w") as f:
        for doc_id, typ, lang, field, title, _ in dump.search(pattern, lang):
            print(
                "* [{}](https://www.camptocamp.org/{}/{}/{})".format(
                    title, get_constructor(typ).url_path, doc_id, lang
                )
            )

            f.write("{}|{}\n".format(doc_id, typ))


if __name__ == "__main__":
    # pre parser release
    bi_pattern = r"\[/?[biBI] *\]"  # 26
    url_pattern = r"\[ */? *url"  # 18
    color_u_pattern = r"\[/?(color|u|U) *(\]|=)"  # 7
    mail_pattern = r"\[/?email"  # 0
    code_pattern = r"\[/?(c|code)\]"  # 0
    c2c_title_pattern = r"#+c "  # 0
    comment_pattern = r"\[\/\*\]"  # 0
    old_tags_pattern = r"\[/?(imp|warn|abs|abstract|list)\]"  # 0
    html_pattern = r"\[/?(sub|sup|s|q|acr)\]"  # 0
    center_pattern = r"\[/?center\]"  # 0
    quote_pattern = r"\[/?(quote|q)\]"  # 0
    anchors_pattern = r"\\{#[\w-]\}[^\n]"  # 0
    right_left_pattern = r"\[/?(right|left)\]"  # 0
    html_ok_pattern = r"\[/?(hr|hr)\]"  # 0
    toc_pattern = r"\[[tT][oO][cC][^\]]"  # 0

    # to fix
    emoji_pattern = r"\[picto"  # 26
    emoji_pattern2 = r"\[img=picto"
    col_pattern = r"\[ */? *col +\d* *(left|right)? *\d* *\]"  # 0
    double_dot_pattern = r"\:\:+"  # 4 (faux positifs)
    slash_in_links_pattern = r"\[\[ */\w+/\d+"  # 0
    broken_ext_links_pattern = r"\[\[ *(http|www)"  # 0
    broken_int_links_pattern = r"\[\[/? */? *\d+\|"  # 0
    forum_links_pattern = r"#t\d+"  # 1
    wrong_pipe_pattern = r"(\n|^)L#\~ *\|"  # 0
    empty_link_label = r"\[ *\]\("  # 0
    important_pattern = r"\[ *(important|warning)"  # 0

    img_not_first_pattern = r"[^\n\]`]\[img"

    da_fuck = r"[^\n]\[p]"

    video_youtube = r"\[video\]https?:\/\/(?:www\.)?youtube\.com"
    video_youtube_short = r"\[video\]https?:\/\/(?:www\.)?youtu\.be"
    daily_video = r"\[video\]https?://(?:www\.)?dailymotion\.com"
    daily_short = r"\[video\]https?://(?:www\.)?dai\.ly"
    vimeo_short = r"\[video\]https?://(?:www\.)?vimeo\.com"

    video_pattern = r"youtube"

    wrong_ltag_pattern = r"(\n|^)[LR]\d+ *[,\|\:]"

    latg_ = ""
    latg_2 = "\n\nL#~"

    leading_lf = "^\n"
    too_many_lf = "\n\n\n"

    wrong_minute_abbr = r"\d+ *mn"

    nospace = r"(^|[| \n\(])(\d+[-xX])?\d+(m|km|h|mn|min|s)($|[ |,.?!:;\)\n])"

    cross = r"\d[X*x]\d\d ?m\b"

    acronym = r"\[acronym"

    ltag1 = "[LR]#[^\n ]*!"  # ok
    ltag2 = "[LR]#[^\n |]*_"  # ok
    ltag3 = "[LR]#[a-zA-Z'\"]"  # ok
    ltag4 = r"[LR]#\+[a-zA-Z'\"]"  # ok
    ltag5 = r"[LR]#\+\d+[a-zA-Z'\"]"  # ok
    ltag6 = r"[LR]#[\-+]"  # ok

    v5_link = r"/\w+/list/"

    false_ltag = r"(\n|^)[LR]\d+ *[,\|\:]"
    false_ol = r"(\n|^)1\)"
    false_md = r"(\n|^) *\* *(\r|\n|$)"
    false_title = r"(\n|^)#+.*: *(\r|\n|$)"
    false_title_1 = r"(\n|^)#[^#]"
    false_title_bold = r"(\n|^)#+[^\n]*\*"

    #    Dump().complete()
    #    _search(r"[dD][ue] (la|là|parking|sommet|col|refuge|relais) (redescendre|remonter|suivre|traverser|tourner|se diriger|prendre)", "fr")

    _search(r"\b\d+ h( \d+)?\b", "fr")

    # with open("contributors.txt", "w") as f:
    #     for d in Dump().sql_file("campbot/sql/contrib_count.sql"):
    #          f.write("|".join(map(str, d)) + "\n")
    #          print(*d)
