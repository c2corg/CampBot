CampBot class
=============

.. autoclass:: campbot.CampBot
   :members: login, clean, export, export_contributions, clean_recent_changes, get_documents,  get_users_from_route

Rate limits
-----------

camptocamp.org limits the number of requests per client. When a request is refused with ``429 Too Many Requests``
(or ``503`` with a ``Retry-After`` header), CampBot waits for the time the server asks, then sends it again,
up to 5 times. It also spaces the next requests more.

If the server asks to wait more than 5 minutes, CampBot does not wait and raises ``requests.HTTPError``.
Both limits can be changed on ``bot.wiki`` and ``bot.forum``:

.. code-block:: python

    bot.wiki.max_retries = 10
    bot.wiki.max_wait = 3600  # seconds

Properties
----------

* ``bot.wiki`` : a :doc:`WikiBot instance </API/WikiBot>`
* ``bot.forum`` : a :doc:`ForumBot instance </API/ForumBot>`
* ``bot.moderator`` : Boolean, True if logged with a moderator account