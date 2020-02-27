from envparse import env

DEBUG = env.bool('DEBUG', default=True)

INFO_SERVICE_API_URL = 'http://127.0.0.1:8334/api/' if DEBUG else 'http://info:8334/api/'
REDIS_HOST = '127.0.0.1' if DEBUG else 'redis'

FASTEST = 'fastest'
SLOWEST = 'slowest'
CHEAPEST = 'cheapest'
EXPENSIVE = 'expensive'
OPTIMAL = 'optimal'

ALLOWED_MODES = [FASTEST, SLOWEST, CHEAPEST, EXPENSIVE]

ROUTE_CACHE_KEY = '{source}_{destination}_{mode}'
