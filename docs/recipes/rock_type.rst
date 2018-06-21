Add a rock type to a list of document
=====================================

This script will add limestone rock type ("calcaire in french") on all routes associated to waypoint ``107702`` (Verdon in France, which is actually a limestone area) :

.. code-block:: python

    from campbot import CampBot
    
    bot = CampBot(use_demo=True)
    bot.login("bot_login", "bot_password")

    filters = {"w": 107702}

    for route in bot.wiki.get_routes(filters):
        route["rock_types"] = route.get("rock_types", []) or []
        if "calcaire" not in route["rock_types"]:
            route["rock_types"].append("calcaire")
            route.save("Only limestone in Verdon")