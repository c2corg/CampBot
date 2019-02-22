Get documents 
=============

Here is a code that load every single documents based on a filter. Corresponding Camptocamp URL is https://www.camptocamp.org/routes#a=14405&act=mountain_climbing%252Crock_climbing 

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    
    # Let get all routes inside area 14405 (French Jura), 
    # AND where activity is rock_climbing OR mountain_climbing

    filters = {
        "a": 14405, 
        "act":["rock_climbing", "mountain_climbing"]
    }
    
    for route in bot.wiki.get_routes(filters):
        print(route)

``bot.wiki`` object has also theese functions :

* ``bot.wiki.get_areas(filters)``
* ``bot.wiki.get_outings(filters)``
* ``bot.wiki.get_waypoints(filters)``
* ``bot.wiki.get_xreports(filters)``

.. warning::

    Due to Camptcamp database limitations, you won't be able to load more than 10,000 documents with this method. Please use a more precise filter if you need to crawl a big amount of data. On the other hand, it should be more efficient to ask to Camptocamp associtation a static dump if you need to download a consequent part of C2C data. 