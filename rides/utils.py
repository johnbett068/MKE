# rides/utils.py

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS points in kilometers
    using the Haversine formula.
    """

    R = 6371  # Earth radius in KM

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def estimate_eta_minutes(distance_km, average_speed_kmh=40):
    """
    Estimate ETA in minutes.
    Default speed = 40 km/h (typical city average).
    """

    if distance_km <= 0:
        return 0

    hours = distance_km / average_speed_kmh
    minutes = hours * 60

    return round(minutes, 1)
