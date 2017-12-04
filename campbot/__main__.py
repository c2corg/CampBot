"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_voters <message_url> --login=<login> --password=<password> [--delay=<seconds>]
  campbot check_recent_changes <message_url> --langs=<langs> --login=<login> --password=<password> [--delay=<seconds>]
  campbot remove_bbcode <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot clean_color_u <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
  campbot remove_bbcode2 <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]


Options:
  --login=<login>           Bot login
  --password=<password>     Bot password
  --delay=<seconds>         Minimum delay between each request. Default : 1 second
  --batch                   Batch mode, means that no confirmation is required before saving
                            Use very carefully
  --langs=<langs>           Limit check to his langs

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

elif args["check_recent_changes"]:
    get_campbot().check_recent_changes(check_message_url=args["<message_url>"],
                                       langs=args["--langs"].split(","))

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
