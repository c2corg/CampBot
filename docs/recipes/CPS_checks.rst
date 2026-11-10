Check that Sophie picture contest criteria has been respected
=============================================================

The rules are :

* a picture can't be resubmitted
* a participant cannot submit more than 3 pictures

The script takes the article of the contest to check, then the articles of the
previous contests. Nothing has to be changed in the code from one year to the
next: give the new article as first argument, and add the previous contest to
the list.

.. code-block:: bash

    python cps_checks.py 1350370 187913 237549 300413 374949 465897 555996 673796 809627 937458 1058594 1154231 1251594

**cps_checks.py** :

.. code-block:: python

    import sys
    from collections import defaultdict
    from campbot import CampBot

    MAX_IMAGES_PER_USER = 3

    if len(sys.argv) < 3:
        sys.exit("usage: python cps_checks.py <contest article> <previous contest article>...")

    contest_id = int(sys.argv[1])
    previous_ids = [int(article_id) for article_id in sys.argv[2:]]

    bot = CampBot(min_delay=0.1)

    print("Load images of previous contests", end="")
    previous_images = {}
    for article_id in previous_ids:
        article = bot.wiki.get_article(article_id)
        for image in article.associations.images:
            previous_images[image.document_id] = article_id
    print(" - Ok")

    contest = bot.wiki.get_article(contest_id)
    errors = 0

    print("Check that no image has been submitted in a previous contest", end="")
    for image in contest.associations.images:
        if image.document_id in previous_images:
            errors += 1
            print(
                f"\nImage {image.document_id} has already been submitted "
                f"in article {previous_images[image.document_id]}"
            )
    print(" - Ok" if errors == 0 else "")

    print("Check that no user has submitted more than {} images:".format(MAX_IMAGES_PER_USER))
    users = defaultdict(list)
    for image in contest.associations.images:
        full_image = bot.wiki.get_image(image.document_id)
        users[full_image.creator["user_id"]].append(image.document_id)

    for user, images in users.items():
        if len(images) > MAX_IMAGES_PER_USER:
            errors += 1
            print(f"User {user} has submitted {len(images)} images: {images}")

    sys.exit(1 if errors else 0)
