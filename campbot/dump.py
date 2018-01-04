import sqlite3
import re

from campbot import CampBot


class Dump(object):
    def __init__(self):
        super(Dump, self).__init__()

        self._conn = sqlite3.connect(r"camptocamp.db")

        self._conn.execute("CREATE TABLE IF NOT EXISTS document ("
                           " document_id INT PRIMARY KEY,"
                           " type CHAR(1),"
                           " version_id INT NOT NULL"
                           ");")

        self._conn.execute("CREATE TABLE IF NOT EXISTS locale ("
                           " document_id INT,"
                           " lang CHAR(2),"
                           " field VARCHAR,"
                           " value TEXT"
                           ");")

        def regexp(y, x, search=re.search):
            return 1 if search(y, str(x)) else 0

        self._conn.create_function('regexp', 2, regexp)
        self._cur = None

    def insert(self, doc=None, version_id=0, contrib=None):
        cur = self._conn.cursor()

        if not doc:
            doc = contrib.get_full_document()
            version_id = contrib.version_id

        if "type" not in doc:
            return

        cur.execute("DELETE FROM document WHERE document_id=?", (doc.document_id,))
        cur.execute("DELETE FROM locale WHERE document_id=?", (doc.document_id,))

        cur.execute("INSERT INTO document"
                    "(document_id, type, version_id)"
                    "VALUES (?,?,?)",
                    (doc.document_id, doc.type, version_id))

        for locale in doc.get("locales", []):

            lang = locale.pop("lang")
            locale.pop("version", None)
            locale.pop("topic_id", None)

            for field in locale:
                value = locale[field]
                if isinstance(value, str) and len(value.strip()) != 0:
                    cur.execute("INSERT INTO locale"
                                "(document_id,lang,field,value)"
                                "VALUES (?,?,?,?)",
                                (doc.document_id, lang, field, value))

        self._conn.commit()

    def select(self, document_id):
        sql = "SELECT * FROM document WHERE document_id=?;"

        self._cur = self._conn.cursor()
        self._cur.execute(sql, (document_id,))

        result = self._cur.fetchone()

        self._conn.commit()
        self._cur.close()
        self._cur = None

        return result

    def get_highest_version_id(self):
        sql = "SELECT version_id from document ORDER BY version_id DESC LIMIT 1"

        self._cur = self._conn.cursor()
        self._cur.execute(sql)

        result = self._cur.fetchone()

        self._conn.commit()
        self._cur.close()
        self._cur = None

        return result[0]

    def complete(self):

        bot = CampBot(min_delay=0.01)

        still_done = []
        highest_version_id = self.get_highest_version_id()

        for contrib in bot.wiki.get_contributions(oldest_date="1990-12-25"):
            if highest_version_id >= contrib.version_id:
                break

            key = (contrib.document.document_id, contrib.document.type)
            if key not in still_done:
                still_done.append(key)
                self.insert(contrib=contrib)
                print(contrib.written_at, key, contrib.version_id, "inserted")
            else:
                print(contrib.written_at, key, contrib.version_id, "still done")

    def search(self, pattern):
        sql = ("SELECT document.document_id, document.type, locale.lang, locale.field "
               "FROM locale "
               "LEFT JOIN document ON document.document_id=locale.document_id "
               "WHERE locale.value REGEXP ?")

        c = self._conn.cursor()
        c.execute(sql, (pattern,))
        return c.fetchall()

    def get_all_ids(self):

        sql = "SELECT document_id, type FROM document"

        self._cur = self._conn.cursor()
        self._cur.execute(sql)

        result = self._cur.fetchall()

        self._conn.commit()
        self._cur.close()
        self._cur = None

        return result


def get_document_types():
    return {doc_id: typ for doc_id, typ in Dump().get_all_ids()}


def _search(pattern):
    from campbot.objects import get_constructor

    dump = Dump()
    dump.complete()

    with open("ids.txt", "w") as f:
        for doc_id, typ, lang, field in dump.search(pattern):
            if lang.strip():
                print("* https://www.camptocamp.org/{}/{}/{} {}".format(get_constructor(typ).url_path, doc_id,
                                                                        lang, field))
            else:
                print("* https://www.camptocamp.org/{}/{} {}".format(get_constructor(typ).url_path, doc_id, field))

            f.write("{}|{}\n".format(doc_id, typ))


if __name__ == "__main__":
    # pre parser release
    bi_pattern = r"\[/?[biBI] *\]"  # 28
    color_u_pattern = r"\[/?(color|u|U) *(\]|=)"  # 7
    mail_pattern = r"\[/?email"  # 1
    url_pattern = r"\[ *url *[\]\=] *[^\n \&\]\[]*?[\]\[]"  # 1
    code_pattern = r"\[/?(c|code)\]"  # 1
    c2c_title_pattern = r"#+c "  # 0
    comment_pattern = r"\[\/\*\]"  # 0
    old_tags_pattern = r"\[/?(imp|warn|abs|abstract|list)\]"  # 0

    # post parser release
    url_amp_pattern = r"\[ */? *url"  # 1000 PR ok
    html_pattern = r"\[/?(sub|sup|s|q|acr)\]"  # 494 PR ok
    center_pattern = r"\[/?center\]"  # 59 PR ok
    quote_pattern = r"\[/?(quote|q)\]"  # 75
    anchors_pattern = r"\{#\w+\}"  # 28 PR ok gaffe aux ids
    right_left_pattern = r"\[/?(right|left)\]"  # 0
    html_ok_pattern = r"\[/?(hr|hr)\]"  # 0

    # to fix
    double_dot_pattern = r"\:\:+"  # 513
    emoji_pattern = r"\[picto"  # 77
    col_pattern = r"\[ */? *col"  # 48
    broken_int_links_pattern = r"\[\[/? */? *\d+\|"  # 4
    slash_in_links_pattern = r"\[\[ */\w+/\d+"  # 3
    broken_ext_links_pattern = r"\[\[ *(http|www)"  # 4
    forum_links_pattern = r"#t\d+"  # 1
    wrong_pipe_pattern = r"(\n|^)L#\~ *\|"  # 0
    empty_link_label = r"\[ *\]\("  # 0

    _search(mail_pattern)
