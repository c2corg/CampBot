"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_voters <message_url> --login=<login> --password=<password> [--delay=<seconds>]
  campbot fix_markdown <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]

Options:
  --login=<login>          Bot login
  --password=<password>    Bot password
  --delay=<seconds>        Minimum delay between each request. Default : 1 second
  --batch                  Batch mode, means that no confirmation is required before saving
                           Use very carefully

"""

from docopt import docopt
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")

args = docopt(__doc__)


def get_campbot():
    from campbot import CampBot

    bot = CampBot(min_delay=args["--delay"])
    bot.login(login=args["--login"], password=args["--password"])

    return bot


if args["check_voters"]:
    get_campbot().check_voters(url=args["<message_url>"])

elif args["fix_markdown"]:
    from campbot.utils import get_ids_from_file
    from campbot.processors import BBCodeRemover

    ids = get_ids_from_file(args["<ids_file>"])
    get_campbot().fix_markdown(BBCodeRemover(), ask_before_saving=args["--batch"] is None,
                               **ids)
