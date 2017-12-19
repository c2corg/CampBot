"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_voters <message_url> --login=<login> --password=<password> [--delay=<seconds>]
  campbot check_recent_changes <message_url> --lang=<lang> --login=<login> --password=<password> [--delay=<seconds>]
  campbot remove_bbcode <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot clean_color_u <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot remove_bbcode2 <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot contributions [--out=<filename>] [--starts=<start_date>] [--ends=<end_date>] [--delay=<seconds>]
  campbot outings <filters> [--out=<filename>] [--delay=<seconds>]


Options:
  --login=<login>           Bot login
  --password=<password>     Bot password
  --batch                   Batch mode, means that no confirmation is required before saving
                            Use very carefully
  --lang=<lang>             Limit check to this lang
  --delay=<seconds>         Minimum delay between each request. Default : 1 second
  --out=<filename>          Output file name. Default value will depend on process

"""

from __future__ import unicode_literals, print_function

from docopt import docopt
import logging
import os
import io

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")

args = docopt(__doc__)


def get_campbot():
    from campbot import CampBot

    proxies = {}

    if "HTTPS_PROXY" in os.environ:
        proxies["https"] = os.environ["HTTPS_PROXY"]

    bot = CampBot(proxies=proxies, min_delay=args["--delay"])

    if args["--login"] and args["--password"]:
        bot.login(login=args["--login"], password=args["--password"])

    return bot


def main():
    if args["check_voters"]:
        get_campbot().check_voters(url=args["<message_url>"])

    elif args["check_recent_changes"]:
        get_campbot().check_recent_changes(check_message_url=args["<message_url>"],
                                           lang=args["--lang"].strip())

    elif args["remove_bbcode"]:
        from campbot.utils import get_ids_from_file
        from campbot.processors import BBCodeRemover

        ids = get_ids_from_file(args["<ids_file>"])
        get_campbot().fix_markdown(BBCodeRemover(),
                                   ask_before_saving=not args["--batch"], **ids)

    elif args["clean_color_u"]:
        from campbot.utils import get_ids_from_file
        from campbot.processors import ColorAndUnderlineRemover

        ids = get_ids_from_file(args["<ids_file>"])
        get_campbot().fix_markdown(ColorAndUnderlineRemover(),
                                   ask_before_saving=not args["--batch"], **ids)


    elif args["remove_bbcode2"]:
        from campbot.utils import get_ids_from_file
        from campbot.processors import BBCodeRemover2

        ids = get_ids_from_file(args["<ids_file>"])
        get_campbot().fix_markdown(BBCodeRemover2(),
                                   ask_before_saving=not args["--batch"], **ids)

    elif args["contributions"]:

        message = ("{timestamp};{type};{document_id};{version_id};{document_version};"
                   "{title};{quality};{user};{lang}\n")

        with io.open(args["--out"] or "contributions.csv", "w", encoding="utf-8") as f:

            def write(**kwargs):
                f.write(message.format(**kwargs))

            write(timestamp="timestamp", type="type",
                  document_id="document_id", version_id="version_id", document_version="document_version",
                  title="title", quality="quality", user="username", lang="lang")

            for c in get_campbot().wiki.get_contributions(oldest_date=args["--starts"], newest_date=args["--ends"]):
                write(timestamp=c.written_at,
                      type=c.document.url_path, document_id=c.document.document_id,
                      version_id=c.version_id, document_version=c.document.version,
                      title=c.document.title.replace(";", ","), quality=c.document.quality,
                      user=c.user.username, lang=c.lang)

    elif args["outings"]:
        from campbot.objects import Outing

        headers = ["date_start", "date_end", "title", "equipement_rating",
                   "global_rating", "height_diff_up", "rock_free_rating",
                   "condition_rating", "elevation_max", "img_count", "quality", "activities"]

        message = ";".join(["{" + h + "}" for h in headers]) + "\n"

        filters = {k: v for k, v in (v.split("=") for v in args["<filters>"].split("&"))}

        with io.open(args["--out"] or "outings.csv", "w", encoding="utf-8") as f:
            f.write(message.format(**{h: h for h in headers}))
            for doc in get_campbot().wiki.get_documents(Outing, filters):
                data = {h: doc.get(h, "") for h in headers}

                data["title"] = doc.get_title("fr").replace(";", ",")
                data["activities"] = ",".join(data["activities"])

                f.write(message.format(**data))


if __name__ == "-__main__":
    main()
