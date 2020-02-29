from datetime import timedelta

import redis
from envparse import env

DEBUG = env.bool('DEBUG', default=True)

INFO_SERVICE_API_URL = 'http://127.0.0.1:8334/api/' if DEBUG else 'http://info:8334/api/'

FASTEST = 'fastest'
SLOWEST = 'slowest'
CHEAPEST = 'cheapest'
EXPENSIVE = 'expensive'
OPTIMAL = 'optimal'
ALLOWED_MODES = [FASTEST, SLOWEST, CHEAPEST, EXPENSIVE]

ROUTE_CACHE_KEY = '{source}_{destination}_{mode}'

MAX_TIME_BETWEEN_FLIGHTS = timedelta(hours=12).total_seconds()

REDIS_HOST = '127.0.0.1' if DEBUG else 'redis'
cache = redis.Redis(host=REDIS_HOST, port=6379)
