from campbot import CampBot, ForumBot
from datetime import datetime, timedelta

bot = CampBot()
fbot = ForumBot()


def get_contributors():
    result = []
    for user in bot.list_contributors(oldest_date=datetime.today() + timedelta(days=-1)):
        result.append(bot.get_profile(user["user_id"]))

    return result


def get_voters(post_id):
    return fbot.get_voters(post_id)


def check_voters(post_id):
    voters = []
    data = get_voters(post_id)["poll"]
    for item in data:
        voters += data[item]

    contributors = {u["forum_username"]: u for u in get_contributors()}

    print("forum", "status")
    for voter in voters:
        print(voter["username"], voter["username"] in contributors)
