Check that Sophie picture contest criteria has been respected
=============================================================

The rules are : 

* a picture can't be resubmitted
* a participant cannot submit more than 3 pictures

.. code-block:: python
    from collections import defaultdict
    from campbot import CampBot

    bot = CampBot(min_delay=0.01)

    article_ids = [
        187913,
        237549,
        300413,
        374949,
        465897,
        555996,
        673796,
        809627,
        937458,
        1058594,
        1058594,
    ]

    print("Load images of previous challenges", end ="")
    images_id = {}
    for article_id in article_ids:
        article = bot.wiki.get_article(article_id)
        for image in article.associations.images:
            images_id[image.document_id] = article_id
    print(" - Ok")

    print("Check that no image has been submitted in a previous challenges", end="")
    article = bot.wiki.get_article(1251594)
    for image in article.associations.images:
        if image.document_id in images_id:
            raise Exception(f"Image {image.document_id} has been submitted on article {images_id[image.document_id]}")
    print(" - Ok")

    print("Check that no user has submitted more than 3 images:")
    users = defaultdict(list)
    for image in article.associations.images:
        full_image = bot.wiki.get_image(image.document_id)
        users[full_image.creator['user_id']].append(image.document_id)

    for user, images in users.items():
        if len(images) > 3:
            print(f"User {user} has submitted {len(images)} images: {images}")

