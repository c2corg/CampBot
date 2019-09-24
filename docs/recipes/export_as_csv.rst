Export data as CSV 
==================

CSV (comma separated values) is a convenient way to export data for later analysis on spreadsheet softwares (Excel...).
Here is a code that exports some informations from images associated to an article

.. code-block:: python

    from campbot import CampBot

    bot = CampBot(min_delay=0.01)

    article = bot.wiki.get_article(1058594)  # Concours Photo Sophie 2018


    def output(*args):
        print(";".join(map(str, args)))


    output("image", "licence", "creator", "creator_id", "Associated route count",
        "Associated waypoint count")

    for image in article.associations.images:
        image = bot.wiki.get_image(image.document_id)
        output(image.get_url(), image.image_type, image.creator["name"],
            image.creator["user_id"], len(image.associations.routes),
            len(image.associations.waypoints))

