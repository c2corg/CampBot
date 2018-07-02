import json
from datetime import datetime
from math import radians, degrees, sin, atan, sqrt, cos, atan2, pi, exp


def today():
    return datetime.today()


def compute_distance(object1, object2):
    RADIUS = 6378137.0  # in meters on the equator

    def mercator_to_gps(point):
        x = point[0]
        y = point[1]

        long = degrees(x / RADIUS)
        lat = degrees(2 * (atan(exp(y / RADIUS)) - pi / 4))

        return lat, long

    def distance(point1, point2):

        if point1 is None or point2 is None:
            return None

        lat1 = radians(point1[0])
        lon1 = radians(point1[1])
        lat2 = radians(point2[0])
        lon2 = radians(point2[1])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return RADIUS * c

    def get_gps_coordinates(wiki_object):
        if "geometry" not in wiki_object or wiki_object["geometry"]["geom"] is None:
            return None

        geometry = json.loads(wiki_object["geometry"]["geom"])
        assert geometry["type"] == "Point"

        # geometry["coordinates"] is EPSG:3785

        return mercator_to_gps(geometry["coordinates"])

    return distance(get_gps_coordinates(object1), get_gps_coordinates(object2))
