"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot clean_rc <days> <lang> <thread_url> [--login=<login>] [--password=<password>] [--delay=<seconds>] [--batch]
  campbot report_rc <days> <lang> <thread_url> [--login=<login>] [--password=<password>] [--delay=<seconds>]
  campbot clean <url_or_file> <lang> <thread_url> [--login=<login>] [--password=<password>] [--delay=<seconds>] [--batch] [--bbcode]
  campbot report <url_or_file> <lang> [--login=<login>] [--password=<password>] [--delay=<seconds>]
  campbot contribs [--out=<filename>] [--starts=<start_date>] [--ends=<end_date>] [--delay=<seconds>]
  campbot export <url> [--out=<filename>] [--delay=<seconds>]


Options:
  --login=<login>           Bot login
  --password=<password>     Bot password
  --batch                   Batch mode, means that no confirmation is required before saving
                            Use very carefully!
  --delay=<seconds>         Minimum delay between each request. Default : 3 seconds
  --bbcode                  Clean old BBCode in markdown
  --out=<filename>          Output file name. Default value will depend on process


Commands:
  report_rc     Make quality report on recent changes.
  clean_rc      Clean recent changes.
  clean         Clean documents.
                <url_or_file> is like https://www.camptocamp.org/routes#a=523281, or, simplier, routes#a=523281. 
                filename is also accepted, and must be like : 
                123 | r
                456 | w
                <lang> is a lang identifier, like fr for french.
  report        Make quality report on documents.
  contribs      Export all contribution in a CSV file. <start_date> and <end_date> are like 2018-05-12
  export        Export all documents in a CSV file.
                <url> is like https://www.camptocamp.org/outings#u=2, or, simplier, outings#u=2

"""

from __future__ import unicode_literals, print_function

from docopt import docopt
import logging
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)-15s %(levelname)s %(message)s"
)


def get_campbot(args):
    from campbot import CampBot

    proxies = {}

    if "HTTPS_PROXY" in os.environ:
        proxies["https"] = os.environ["HTTPS_PROXY"]

    if "CAMPBOT_CREDENTIALS" in os.environ and not args["--login"]:
        args["--login"], args["--password"] = os.environ["CAMPBOT_CREDENTIALS"].split(
            "@", 1
        )

    if "CAMPBOT_LOGIN" in os.environ and not args["--login"]:
        args["--login"] = os.environ["CAMPBOT_LOGIN"]

    if "CAMPBOT_PASSWORD" in os.environ and not args["--password"]:
        args["--password"] = os.environ["CAMPBOT_PASSWORD"]

    bot = CampBot(proxies=proxies, min_delay=args["--delay"])

    if args["--login"] and args["--password"]:
        bot.login(login=args["--login"], password=args["--password"])

    return bot


def main_entry_point():
    main(docopt(__doc__))


def main(args):
    if args["report_rc"]:
        from campbot.checkers import report_recent_changes

        report_recent_changes(
            get_campbot(args),
            days=float(args["<days>"]),
            lang=args["<lang>"],
            thread_url=args["<thread_url>"],
        )

    elif args["clean_rc"]:
        get_campbot(args).clean_recent_changes(
            days=float(args["<days>"]),
            lang=args["<lang>"],
            ask_before_saving=not args["--batch"],
            thread_url=args["<thread_url>"],
        )

    elif args["report"]:
        get_campbot(args).report(
            args["<url_or_file>"],
            lang=args["<lang>"],
        )

    elif args["clean"]:
        get_campbot(args).clean(
            args["<url_or_file>"],
            lang=args["<lang>"],
            ask_before_saving=not args["--batch"],
            thread_url=args["<thread_url>"],
            clean_bbcode=args["--bbcode"],
        )

    elif args["contribs"]:
        get_campbot(args).export_contributions(
            starts=args["--starts"], ends=args["--ends"], filename=args["--out"]
        )

    elif args["export"]:
        get_campbot(args).export(args["<url>"], args["--out"])


if __name__ == "__main__":
    main_entry_point()
