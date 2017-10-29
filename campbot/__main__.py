"""
CampBot, Python bot framework for camptocamp.org

Usage:
  campbot check_voters <message_url> --login=<login> --password=<password>

Options:
  --login=<login>          Bot login
  --password=<password>    Bot password

"""

from docopt import docopt

args = docopt(__doc__)

if args["check_voters"]:
    from campbot import CampBot

    bot = CampBot()
    bot.login(login=args["--login"], password=args["--password"])

    bot.check_voters(url=args["<message_url>"])
