import json
from datetime import timedelta
from parser import FlightParser

import aiohttp
import redis
from exceptions import WrongIncomeData
from graph import DurationBasedGraph, PriceBasedGraph
from sanic import Sanic, response
from sanic_openapi import swagger_blueprint, doc
from serializers import RouteSerializer
from settings import (
    FASTEST,
    SLOWEST,
    CHEAPEST,
    EXPENSIVE,
    OPTIMAL,
    ROUTE_CACHE_KEY,
    INFO_SERVICE_API_URL,
    REDIS_HOST,
    ALLOWED_MODES,
)
from utils import json_defaults

app = Sanic()
app.blueprint(swagger_blueprint)
cache = redis.Redis(host=REDIS_HOST, port=6379)


# Server Hooks
@app.listener('before_server_start')
def init(app, loop):
    app.aiohttp_session = aiohttp.ClientSession(loop=loop)


@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.aiohttp_session.close())
    loop.close()


# Utils
async def get_flights_data():
    flights_data = []

    async with app.aiohttp_session.get(INFO_SERVICE_API_URL + 'flights/1/') as res:
        flights_data += [await res.text()]

    async with app.aiohttp_session.get(INFO_SERVICE_API_URL + 'flights/2/') as res:
        flights_data += [await res.text()]

    return flights_data


async def get_airports():
    async with app.aiohttp_session.get(INFO_SERVICE_API_URL + 'airports/list/') as res:
        return await res.json()


# Exception Handlers
@app.exception(WrongIncomeData)
async def wrong_data_handler(request):
    return response.json({'error': 'Provide both source and destination'}, status=400)


# API Endpoints
@app.route('/api/healthcheck/', methods=['GET'])
@doc.summary('Healthcheck')
async def healthcheck(request):
    return response.json(body={'status': 'OK'})


@app.route('/api/flights/<mode>/', methods=['GET'])
@doc.summary('Get all flights by mode')
@doc.consumes(doc.String(name='source'), required=True, location='query')
@doc.consumes(doc.String(name='destination'), required=True, location='query')
async def get_flights(request, mode):
    if mode not in ALLOWED_MODES:
        return response.json({'error': 'Mode Not Found'}, status=400)

    if 'source' not in request.raw_args or 'destination' not in request.raw_args:
        raise WrongIncomeData()

    airports_data = await get_airports()
    flights_data = await get_flights_data()
    parsed_flights_data = FlightParser(flights_data).parse()

    reverse, graph_class = False, None
    source, destination = request.raw_args['source'], request.raw_args['destination']

    if mode in [FASTEST, SLOWEST]:
        graph_class = DurationBasedGraph
    elif mode in [CHEAPEST, EXPENSIVE]:
        graph_class = PriceBasedGraph

    if mode in [SLOWEST, EXPENSIVE]:
        reverse = True

    cache_key = ROUTE_CACHE_KEY.format(source=source, destination=destination, mode=mode)
    cached_data = cache.get(cache_key)

    if cached_data:
        return response.json(json.loads(cached_data))
    else:
        graph = graph_class(edges=parsed_flights_data, airports=airports_data, reverse=reverse)
        routes = graph.get_routes(source, destination)

        serializer = RouteSerializer()
        data = serializer.dump(routes, many=True)
        cache.setex(cache_key, timedelta(minutes=10), json.dumps(data, default=json_defaults, sort_keys=True))

        return response.json(data)


@app.route(f'/api/flights/{OPTIMAL}', methods=['GET'])
@doc.summary('Get optimal flights')
@doc.consumes(doc.String(name='source'), required=True, location='query')
@doc.consumes(doc.String(name='destination'), required=True, location='query')
async def get_optimal_flights(request):
    if 'source' not in request.raw_args or 'destination' not in request.raw_args:
        raise WrongIncomeData()

    source, destination = request.raw_args['source'], request.raw_args['destination']

    cache_key = ROUTE_CACHE_KEY.format(source=source, destination=destination, mode=OPTIMAL)
    cached_data = cache.get(cache_key)

    if cached_data:
        return response.json(json.loads(cached_data))
    else:
        airports_data = await get_airports()
        flights_data = await get_flights_data()
        parsed_flights_data = FlightParser(flights_data).parse()

        cheapest_graph = PriceBasedGraph(edges=parsed_flights_data, airports=airports_data)
        cheapest_graph_routes = cheapest_graph.get_routes(source, destination)

        fastest_graph = DurationBasedGraph(edges=parsed_flights_data, airports=airports_data)
        fastest_graph_routes = fastest_graph.get_routes(source, destination)

        most_optimal = set(
            cheapest_graph_routes[:len(cheapest_graph_routes) // 2],
        ).intersection(
            set(fastest_graph_routes[:len(fastest_graph_routes) // 2]),
        )
        sorted_optimal = sorted(most_optimal, key=lambda i: (i.flights, i.total_price, i.total_duration))

        serializer = RouteSerializer()
        data = serializer.dump(sorted_optimal, many=True)
        cache.setex(cache_key, timedelta(minutes=10), json.dumps(data, default=json_defaults, sort_keys=True))

        return response.json(data)
