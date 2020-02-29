from settings import OPTIMAL
from views import healthcheck, get_flights, get_optimal_flights

routes = [
    (healthcheck, '/api/healthcheck/', ['GET']),
    (get_flights, '/api/flights/<mode>/', ['GET']),
    (get_optimal_flights, f'/api/flights/{OPTIMAL}', ['GET']),
]


def setup_routes(app):
    for route in routes:
        app.add_route(route[0], route[1], route[2])  # Handler | URL | Methods
