"""
CampBot, Python bot framework for camptocamp.org
"""

import argparse
import logging
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)-15s %(levelname)s %(message)s"
)

EPILOG = """environment variables:
  CAMPBOT_LOGIN, CAMPBOT_PASSWORD   bot credentials, used when --login and
                                    --password are not given
  CAMPBOT_CREDENTIALS               "login@password", same as above
  HTTPS_PROXY                       proxy used for all requests
"""

URL_OR_FILE_HELP = """URL like https://www.camptocamp.org/routes#a=523281 or, simpler, routes#a=523281.
A file name is also accepted, with one document per line, like "123|r" or "456|w"
"""


def _credentials_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--login", help="Bot login")
    parser.add_argument("--password", help="Bot password")
    parser.add_argument(
        "--delay",
        metavar="SECONDS",
        help="Minimum delay between each request. Default: 3 seconds",
    )
    parser.add_argument(
        "--user-agent",
        metavar="NAME",
        help="Name and version of your tool, like MyTool/1.2, sent before CampBot's own",
    )
    return parser


def build_parser():
    common = _credentials_parser()

    batch = argparse.ArgumentParser(add_help=False)
    batch.add_argument(
        "--batch",
        action="store_true",
        help="No confirmation is required before saving. Use very carefully!",
    )

    parser = argparse.ArgumentParser(
        prog="campbot",
        description="CampBot, Python bot framework for camptocamp.org",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    def command(name, help, parents=()):
        return commands.add_parser(
            name,
            help=help,
            description=help,
            parents=[common, *parents],
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    p = command("report_rc", "Make quality report on recent changes.")
    p.add_argument("days", help="Number of days to look back")
    p.add_argument("lang", help="Language identifier, like fr for French")
    p.add_argument("thread_url", help="Forum thread where the report is posted")

    p = command("clean_rc", "Clean recent changes.", parents=[batch])
    p.add_argument("days", help="Number of days to look back")
    p.add_argument("lang", help="Language identifier, like fr for French")
    p.add_argument("thread_url", help="Forum thread where the report is posted")

    p = command("clean", "Clean documents.", parents=[batch])
    p.add_argument("url_or_file", help=URL_OR_FILE_HELP)
    p.add_argument("lang", help="Language identifier, like fr for French")
    p.add_argument("thread_url", help="Forum thread where the report is posted")
    p.add_argument("--bbcode", action="store_true", help="Clean old BBCode in markdown")

    p = command("report", "Make quality report on documents.")
    p.add_argument("url_or_file", help=URL_OR_FILE_HELP)
    p.add_argument("lang", help="Language identifier, like fr for French")

    p = command("contribs", "Export all contributions in a CSV file.")
    p.add_argument(
        "--out", metavar="FILENAME", help="Output file name. Default: contributions.csv"
    )
    p.add_argument(
        "--starts",
        metavar="DATE",
        help="Start date, like 2018-05-12. Default: 24 hours ago",
    )
    p.add_argument(
        "--ends", metavar="DATE", help="End date, like 2018-05-12. Default: now"
    )

    p = command("export", "Export all documents in a CSV file.")
    p.add_argument(
        "url",
        help="URL like https://www.camptocamp.org/outings#u=2 or, simpler, outings#u=2",
    )
    p.add_argument(
        "--out",
        metavar="FILENAME",
        help="Output file name. Default: <document type>.csv, like outings.csv",
    )

    return parser


def get_campbot(args):
    from campbot import CampBot

    proxies = {}

    if "HTTPS_PROXY" in os.environ:
        proxies["https"] = os.environ["HTTPS_PROXY"]

    if "CAMPBOT_CREDENTIALS" in os.environ and not args.login:
        args.login, args.password = os.environ["CAMPBOT_CREDENTIALS"].split("@", 1)

    if "CAMPBOT_LOGIN" in os.environ and not args.login:
        args.login = os.environ["CAMPBOT_LOGIN"]

    if "CAMPBOT_PASSWORD" in os.environ and not args.password:
        args.password = os.environ["CAMPBOT_PASSWORD"]

    bot = CampBot(
        proxies=proxies,
        min_delay=args.delay,
        user_agent=getattr(args, "user_agent", None),
    )

    if args.login and args.password:
        bot.login(login=args.login, password=args.password)

    return bot


def main_entry_point():
    main(build_parser().parse_args())


def main(args):
    command = args.command

    if command == "report_rc":
        from campbot.checkers import report_recent_changes

        report_recent_changes(
            get_campbot(args),
            days=float(args.days),
            lang=args.lang,
            thread_url=args.thread_url,
        )

    elif command == "clean_rc":
        get_campbot(args).clean_recent_changes(
            days=float(args.days),
            lang=args.lang,
            ask_before_saving=not args.batch,
            thread_url=args.thread_url,
        )

    elif command == "report":
        get_campbot(args).report(args.url_or_file, lang=args.lang)

    elif command == "clean":
        get_campbot(args).clean(
            args.url_or_file,
            lang=args.lang,
            ask_before_saving=not args.batch,
            thread_url=args.thread_url,
            clean_bbcode=args.bbcode,
        )

    elif command == "contribs":
        get_campbot(args).export_contributions(
            starts=args.starts, ends=args.ends, filename=args.out
        )

    elif command == "export":
        get_campbot(args).export(args.url, args.out)


if __name__ == "__main__":
    main_entry_point()
