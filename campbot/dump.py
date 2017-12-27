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

        bot = CampBot()

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


if __name__ == "__main__":
    dump = Dump()
    #    print(dump.get_all_ids())
    # dump.complete()
    with open("ids.txt", "w") as f:
        for k in dump.search(r"\[/?[bi]\]"):
            print(k)
            f.write("{}|{}\n".format(*k))
