CampBot class
=============

.. autoclass:: campbot.CampBot
   :members: login, clean, export, export_contributions, clean_recent_changes, get_documents,  get_users_from_route

Properties
----------

* ``bot.wiki`` : a :doc:`WikiBot instance </API/WikiBot>`
* ``bot.forum`` : a :doc:`ForumBot instance </API/ForumBot>`
* ``bot.moderator`` : Boolean, True if logged with a moderator account

Name your tool
--------------

Every request CampBot sends has a ``User-Agent`` header that names it::

    CampBot/2.1.3 (+https://github.com/c2corg/CampBot)

If you build a tool on CampBot, give its name and version with ``user_agent``. It is put before CampBot's own name:

.. code-block:: python

    from campbot import CampBot

    bot = CampBot(user_agent="MyTool/1.2 (+https://example.org/mytool)")

Requests then send::

    MyTool/1.2 (+https://example.org/mytool) CampBot/2.1.3 (+https://github.com/c2corg/CampBot)

Some guidelines:

* use the ``Name/version`` form, with no space in the name ;
* add a URL in parentheses, starting with ``+``, where people can find out about your tool or reach you ;
* keep the same name across versions.

The camptocamp.org team can then tell your traffic apart from other CampBot users, and contact you rather than block it if something goes wrong.

On the command line, use the ``--user-agent`` option, like ``campbot export outings#u=2 --user-agent=MyTool/1.2``.
