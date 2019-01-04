Update a locale field
=====================================

This script will update remarks field.
Note the coding header, if you're in Python 2.7, and your update contains special characters

.. code-block:: python

    # coding: utf-8

    import sys
    from campbot import CampBot


    bot = CampBot()
    bot.login("botname", "botpass")

    remarks="!! VTNO rocks!"

    filters = {
        "w": 107049,
        "act":["rock_climbing"]
    }

    for route in bot.wiki.get_routes(filters):
        remarks=route.get_locale("fr").remarks

        if remarks is None:
            route.get_locale("fr").remarks = remarks
            route.save("Remarque gestion par VTNO")

        elif remarks is not None and "VTNO" not in remarks:
            # We consider that if VTNO still exists, then locale is still processed
            route.get_locale("fr").remarks = remarks + "\n\n" + remark
            route.save("Remarque gestion par VTNO")
