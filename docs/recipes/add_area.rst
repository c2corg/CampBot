Create an area
==============

There is no UI for adding new areas. But API entry point is up and running!

.. code-block:: python

    from campbot import CampBot


    def create_area(bot, title, geom_detail):
        result = bot.wiki.post(
            "/areas",
            {
                "geometry": {"geom": None, "geom_detail": json.dumps(geom_detail),},
                "type": "a",
                "quality": "medium",
                "area_type": "admin_limits",
                "available_langs": ["fr"],
                "locales": [
                    {"lang": "fr", "summary": None, "title": title, "description": None,}
                ],
            },
        )

        print(result)

    bot = CampBot()
    bot.login("moderator_login", "password")

    geom_detail = {
        "coordinates": [
            [
                [5012713.121726842, -1417626.9752307558],
                [5014720.969939139, -1419322.4914989625],
                [5016862.674699049, -1421910.3847504659],
                [5012713.121726842, -1417626.9752307558],  # this point must be the same as the first one
            ]
        ],
        "type": "Polygon",
    }

    create_area(bot, "New area", geom_detail)
