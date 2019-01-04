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
    update_comment = "Remarque gestion par VTNO"

    filters = {
        "w": 107049,
        "act":["rock_climbing"]
    }

    for route in bot.wiki.get_routes(filters):
        locale = route.get_locale("fr")

        if locale: # document may have not fr locale : skip it.
            if not locale.remarks: # remarks is none, or empty string
                locale.remarks = remarks
                route.save(update_comment)

            elif "VTNO" not in locale.remarks:
                # We consider that if remarks field still containes "VTNO",
                # then locale is still processed
                locale.remarks = locale.remarks + "\n\n" + remarks
                route.save(update_comment)
