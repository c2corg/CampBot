def get_ids_from_file(filename):
    result = {}
    with open(filename) as f:
        for line in f:
            line = line.replace(" ", "").replace("\n", "")
            item_id, item_type = line.split("|")

            item_type = {"u": "user_ids",
                         "a": "area_ids",
                         "w": "waypoint_ids",
                         "o": "outing_ids",
                         "i": "image_ids",
                         "x": "xreport_ids",
                         "c": "article_ids",
                         "b": "book_ids",
                         "r": "route_ids"}[item_type]

            if item_type not in result:
                result[item_type] = []
            result[item_type].append(int(item_id))

    return result
