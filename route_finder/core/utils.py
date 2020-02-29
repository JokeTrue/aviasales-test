from datetime import datetime, date
from decimal import Decimal

from settings import INFO_SERVICE_API_URL


def json_defaults(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    elif isinstance(o, Decimal):
        return float(o)


async def get_flights_data(session):
    flights_data = []

    async with session.get(INFO_SERVICE_API_URL + 'flights/1/') as res:
        flights_data += [await res.text()]

    async with session.get(INFO_SERVICE_API_URL + 'flights/2/') as res:
        flights_data += [await res.text()]

    return flights_data


async def get_airports(session):
    async with session.get(INFO_SERVICE_API_URL + 'airports/list/') as res:
        return await res.json()
