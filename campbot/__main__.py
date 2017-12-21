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
        get_campbot().fix_markdown(BBCodeRemover2(), ask_before_saving=not args["--batch"], **ids)

    elif args["contributions"]:
        get_campbot().export_contributions(starts=args["--starts"], ends=args["--ends"], filename=args["--out"])

    elif args["outings"]:
        get_campbot().export_outings(args["<filters>"], args["--out"])


if __name__ == "__main__":
    main()
