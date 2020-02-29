import json
from datetime import timedelta
from parser import FlightParser

from exceptions import WrongIncomeData
from graph import DurationBasedGraph, PriceBasedGraph
from sanic import response
from sanic_openapi import doc
from serializers import RouteSerializer
from settings import (
    FASTEST,
    SLOWEST,
    CHEAPEST,
    EXPENSIVE,
    OPTIMAL,
    ROUTE_CACHE_KEY,
    ALLOWED_MODES,
    cache,
)
from utils import json_defaults, get_airports, get_flights_data


@doc.summary('Healthcheck')
async def healthcheck(request):
    return response.json(body={'status': 'OK'})


@doc.summary('Get all flights by mode')
@doc.consumes(doc.String(name='source'), required=True, location='query')
@doc.consumes(doc.String(name='destination'), required=True, location='query')
async def get_flights(request, mode):
    if mode not in ALLOWED_MODES:
        return response.json({'error': 'Mode Not Found'}, status=400)

    if 'source' not in request.raw_args or 'destination' not in request.raw_args:
        raise WrongIncomeData()

    airports_data = await get_airports(request.app.session)
    flights_data = await get_flights_data(request.app.session)
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
        airports_data = await get_airports(request.app.session)
        flights_data = await get_flights_data(request.app.session)
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
