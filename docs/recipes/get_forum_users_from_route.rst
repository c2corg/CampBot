Get user from route
===================

It can be usefull, when you want to discuss about a point on a route, to mention all users that knows this route. This code will display all forum names, 20 per rows (Discourse limit), with a preceding ``@``.

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    
    bot.get_forum_users_from_route(56048)

