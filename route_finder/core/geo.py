import math
from typing import Tuple, List

from exceptions import AirportNotFound


def distance(origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
    '''
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    '''
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
            math.sin(dlat / 2) * math.sin(dlat / 2) +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) * math.sin(dlon / 2)
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d


def get_airport_coordinates(airports: List[dict], airport: str) -> Tuple[float, float]:
    found = [item for item in airports if item['iatacode'] == airport]

    if found:
        return found[0]['lat'], found[0]['lng']
    else:
        raise AirportNotFound()
