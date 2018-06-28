Get user from route
===================

It can be usefull, when you want to discuss about a point on a route, to mention all users that knows this route. This code will display all forum names, 20 per rows (Discourse limit), with a preceding ``@``.

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    
    users = bot.get_users_from_route(56048)

    for sub_users in [users[i:i + 20] for i in range(0, len(users), 20)]:
        print(", ".join(["@" + user["forum_username"] for user in sub_users]))

