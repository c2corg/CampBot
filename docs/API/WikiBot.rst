WikiBot class
=============

About document_type/constructor parameters
------------------------------------------

Some function of WikiBot will ask you to specify which kind of object you want to request. There is two way to specify it :

1. Set document_type argument with a letter (see bellow the mapping)
2. Set constructor argument, see campbot.objects module

Mapping :

* "u": WikiUser
* "a": Area
* "w": Waypoint
* "o": Outing
* "i": Image
* "m": Map
* "x": Xreport
* "c": Article
* "b": Book
* "r": Route

Example : this two line are equivalents

.. code-block:: python
    from campbot import Campbot, objects

    bot = Campbot(user_demo=True)

    bot.wiki.get_documents(filters, document_type='r')
    bot.wiki.get_documents(filters, constructor=objects.Route)


About filters
-------------

Some function that return list of objects have a ``filters`` argument. It's a key value dictionary. Simply see camptocamp URL to understand how to fill it.

API
---

.. autoclass:: campbot.core.WikiBot
   :members: get_wiki_object, get_article, get_route, get_waypoint, get_area, get_profile,
             get_image, get_book, get_map, get_xreport, get_routes, get_waypoints, get_outings, get_documents
