from datetime import datetime, date
from decimal import Decimal


def json_defaults(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    elif isinstance(o, Decimal):
        return float(o)
