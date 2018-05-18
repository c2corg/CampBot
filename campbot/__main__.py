"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_rc --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot check_voters <message_url> --login=<login> --password=<password> [--delay=<seconds>]
  campbot contributions [--out=<filename>] [--starts=<start_date>] [--ends=<end_date>] [--delay=<seconds>]
  campbot outings <filters> [--out=<filename>] [--delay=<seconds>]


Options:
  --login=<login>           Bot login
  --password=<password>     Bot password
  --batch                   Batch mode, means that no confirmation is required before saving
                            Use very carefully
  --delay=<seconds>         Minimum delay between each request. Default : 1 second
  --out=<filename>          Output file name. Default value will depend on process

"""

from __future__ import unicode_literals, print_function

from docopt import docopt
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")


def get_campbot(args):
    from campbot import CampBot

    proxies = {}

    if "HTTPS_PROXY" in os.environ:
        proxies["https"] = os.environ["HTTPS_PROXY"]

    bot = CampBot(proxies=proxies, min_delay=args["--delay"])

    if args["--login"] and args["--password"]:
        bot.login(login=args["--login"], password=args["--password"])

    return bot


def main_entry_point():
    main(docopt(__doc__))


def main(args):
    if args["check_voters"]:
        get_campbot(args).check_voters(url=args["<message_url>"], allowed_groups=("Association",))

    elif args["check_rc"]:
        from campbot.checkers import check_recent_changes

        check_recent_changes(get_campbot(args),
                             ask_before_saving=not(args["--batch"]))

    elif args["contributions"]:
        get_campbot(args).export_contributions(starts=args["--starts"], ends=args["--ends"], filename=args["--out"])

    elif args["outings"]:
        get_campbot(args).export_outings(args["<filters>"], args["--out"])


if __name__ == "__main__":
    main_entry_point()
