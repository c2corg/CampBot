Get routes from books
=====================

Get all routes associated to a set of books

.. code-block:: python

    """
    Usage:
        python get_routees.py 14637 14538 179160 14652 > results.txt
    """

    import campbot 
    import sys

    bot = campbot.CampBot()

    books_ids = sys.argv[1:]

    routes = []
    for books_id in books_ids:
        book = bot.wiki.get_book(books_id)
        routes += book["associations"]["routes"]

    def get_title(r):
        return r.get_title("fr") or r.get_title("it") or r.get_title("de") or r.get_title("es")

    routes = [campbot.objects.Route(bot, r) for r in {r["document_id"]: r for r in routes}.values()]
    routes = sorted(routes, key=get_title)

    for r in routes:
        print(f'1. {r.get_url()} : {get_title(r)}')
