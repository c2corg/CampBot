"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_voters <message_url> --login=<login> --password=<password>
  campbot fix_markdown <ids_file> --login=<login> --password=<password>

Options:
  --login=<login>          Bot login
  --password=<password>    Bot password

"""

from docopt import docopt

args = docopt(__doc__)


def get_campbot():
    from campbot import CampBot

    bot = CampBot()
    bot.login(login=args["--login"], password=args["--password"])

    return bot


if args["check_voters"]:
    get_campbot().check_voters(url=args["<message_url>"])

elif args["fix_markdown"]:
    from campbot.utils import get_ids_from_file
    from campbot.processors import BBCodeRemover

    ids = get_ids_from_file(args["<ids_file>"])
    get_campbot().fix_markdown(BBCodeRemover(), **ids)
