import psycopg2
from campbot import CampBot


class Dump(object):
    def __init__(self, **kwargs):
        super(Dump, self).__init__()

        connection_string = "dbname='{dbname}' user='{user}' host='{host}' port={port} password='{password}'"

        kwargs["dbname"] = kwargs.get("dbname", 'c2c')
        kwargs["user"] = kwargs.get("user", 'charles')
        kwargs["host"] = kwargs.get("host", 'localhost')
        kwargs["port"] = kwargs.get("port", 5432)
        kwargs["password"] = kwargs.get("password", 'charles')

        self._conn = psycopg2.connect(connection_string.format(**kwargs))
        self._cur = None

    def start_database(self):
        self._execute("DROP TABLE document")

        sql = """CREATE TABLE document(
              document_id int,
              version_id int,
              type char(1),
              locales text,
              PRIMARY KEY(document_id)
              );"""

        self._execute(sql)

    def _execute(self, *args):
        self._cur = self._conn.cursor()
        self._cur.execute(*args)

        self._conn.commit()
        self._cur.close()
        self._cur = None

    def insert(self, document, version_id=0):
        def join_locale(locale):
            locale.pop("version", None)
            locale.pop("topic_id", None)
            locale.pop("lang", None)

            values = [str(v) for v in locale.values() if v]
            return "\n\n".join(values)

        if "document_id" not in document or document.document_id == 2:
            return

        if "type" not in document:
            print(document)

        locales = "\n\n".join([join_locale(locale) for locale in document.locales]) if "locales" in document else ""

        if self.select(document.document_id):
            sql = "UPDATE document SET version_id=%s, type=%s, locales=%s WHERE document_id=%s"
            args = (version_id,
                    document.type,
                    locales,
                    document.document_id,
                    )
        else:

            sql = """INSERT INTO document (document_id, version_id, type, locales) VALUES(%s, %s, %s, %s)"""
            args = (document.document_id,
                    version_id,
                    document.type,
                    locales
                    )

        self._execute(sql, args)

    def select(self, document_id):
        sql = "SELECT * FROM document WHERE document_id=%s;"

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

        bot = CampBot(min_delay=0.1)

        still_done = []
        highest_version_id = self.get_highest_version_id()

        for contrib in bot.wiki.get_contributions(oldest_date="1990-12-25"):
            if highest_version_id >= contrib.version_id:
                break

            key = (contrib.document.document_id, contrib.document.type)
            if key not in still_done:
                still_done.append(key)
                self.insert(contrib.get_full_document(), contrib.version_id)
                print(contrib.written_at, key, contrib.version_id, "inserted")
            else:
                print(contrib.written_at, key, contrib.version_id, "still done")

    def search(self, pattern):
        pattern = "%{}%".format(pattern)

        sql = "SELECT document_id, type FROM document WHERE locales SIMILAR TO %s"

        self._cur = self._conn.cursor()
        self._cur.execute(sql, (pattern,))

        result = self._cur.fetchall()

        self._conn.commit()
        self._cur.close()
        self._cur = None

        return result

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
    return {id: type for id, type in Dump().get_all_ids()}


if __name__ == "__main__":
    from campbot.objects import get_constructor

    dump = Dump()
    dump.complete()

    # pre parser release
    bi_pattern = r"\[/?[biBI] *\]"  # 28
    color_u_pattern = r"\[/?(color|u|U) *(\]|=)"  # 7
    mail_pattern = r"\[/?email"  # 1
    url_pattern = r"\[url[\]\=][^\n \&\]\[]*?[\]\[]"  # 1
    code_pattern = r"\[/?(c|code)\]"  # 1
    c2c_title_pattern = r"#+c "  # 0
    comment_pattern = r"\[\/\*\]"  # 0
    old_tags_pattern = r"\[/?(imp|warn|abs|abstract|list)\]"  # 0

    # post parser release
    url_amp_pattern = r"\[/?url[\]\=][^\n \]\[]*?\&"  # 950
    html_pattern = r"\[/?(sub|sup|s|p|q|acr)\]"  # 494
    center_pattern = r"\[/?(center|right|left)\]"  # 65
    quote_pattern = r"\[/?(quote|q)\]"  # 75
    anchors_pattern = r"\{#\w+\}"  # 28
    html_ok_pattern = r"\[/?(hr|hr)\]"  # 0

    # to fix
    double_dot_pattern = r"\:\:+"  # 513
    emoji_pattern = r"\[picto"  # 77
    col_pattern = r"\[/?col\]"  # 42
    broken_int_links_pattern = r"\[\[\d+\|"  # 2
    slash_in_links_pattern = r"\[\[/\w+/\d+"  # 3
    broken_ext_links_pattern = r"\[\[(http|www)"  # 3
    forum_links_pattern = r"#t\d+"  # 1
    wrong_pipe_pattern = r"(\n|^)L#\~ *\|"  # 0
    empty_link_label = r"\[ *\]\([^\n ]+\)"  # 0

    with open("ids.txt", "w") as f:
        for doc_id, typ in dump.search(empty_link_label):
            print("* https://www.camptocamp.org/{}/{}".format(get_constructor(typ).url_path, doc_id))
            f.write("{}|{}\n".format(doc_id, typ))
