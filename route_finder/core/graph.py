import abc
from collections import OrderedDict
from collections import defaultdict
from datetime import timedelta
from queue import PriorityQueue
from typing import List, Union, Dict, Any, TypeVar

from data_classes import Flight, Route
from exceptions import NoRoutesLeft, WrongRoute
from geo import distance, get_airport_coordinates
from settings import MAX_TIME_BETWEEN_FLIGHTS

T = TypeVar('T')  # Any type.
KT = TypeVar('KT')  # Key type.


class SimpleGraph(abc.ABC):
    def __init__(self, edges: Dict[KT, T]):
        self.edges = edges

    def neighbors(self, key: KT) -> List[T]:
        return self.edges[key]

    def heuristic(self, from_node: KT, to_node: KT) -> Union[int, float]:
        raise NotImplementedError

    def _search(self, source: KT, destination: KT) -> List[T]:
        raise NotImplementedError


class AirportsGraph(SimpleGraph):
    def __init__(self, edges, airports, reverse=False):
        super().__init__(edges)
        self.reverse = reverse
        self.airports_data = airports

        flights = defaultdict(set)
        for flight in self.edges:
            flights[flight.source].add(flight)

        self.edges = flights

    def heuristic(self, from_node, to_node) -> Union[int, float]:
        from_coords = get_airport_coordinates(self.airports_data, from_node)
        to_coords = get_airport_coordinates(self.airports_data, to_node)

        return distance(from_coords, to_coords)

    @staticmethod
    def get_priority_value(obj: Flight) -> Any:
        raise NotImplementedError

    @staticmethod
    def _get_best_options(
            flights: List[Flight],
            came_from_flight: Flight,
            exclude_flights: List[Flight] = None,
    ) -> List[Flight]:
        if exclude_flights is None:
            exclude_flights = []

        best_flight_options = {}
        filtered_flights = [item for item in flights if item not in exclude_flights]

        if came_from_flight:
            filtered_flights = list(
                filter(
                    lambda f: 0 < (f.departure - came_from_flight.arrival).total_seconds() <= MAX_TIME_BETWEEN_FLIGHTS,
                    filtered_flights,
                ),
            )

        for flight in filtered_flights:
            if (
                    flight.destination not in best_flight_options or
                    flight.duration < best_flight_options[flight.destination].duration
            ):
                best_flight_options[flight.destination] = flight

        return list(best_flight_options.values())

    @staticmethod
    def _reconstruct_path(came_from: Dict[KT, T], source: KT, destination: KT) -> List[Flight]:
        try:
            flight = came_from[destination]
        except KeyError:
            raise WrongRoute()

        path = [flight]

        while flight.source != source:
            flight = came_from[flight.source]
            path.insert(0, flight)

        return path

    def _search(self, source: KT, destination: KT, exclude_flights=None) -> List[Flight]:
        q = PriorityQueue()
        q.put((0, source))

        came_from = OrderedDict()
        cost_so_far = {source: 0}

        while not q.empty():
            priority, current_airport = q.get()

            if current_airport == destination:
                break

            last_flights = list(came_from.values())
            best_options = self._get_best_options(
                flights=self.neighbors(current_airport),
                came_from_flight=last_flights[-1] if last_flights else None,
                exclude_flights=exclude_flights,
            )
            for flight in best_options:
                new_cost = cost_so_far[current_airport] + self.get_priority_value(flight)

                if flight.destination not in cost_so_far or new_cost < cost_so_far[flight.destination]:
                    cost_so_far[flight.destination] = new_cost
                    came_from[flight.destination] = flight

                    priority = new_cost + self.heuristic(flight.destination, destination)
                    q.put((priority, flight.destination))

        if came_from:
            reconstructed_path = self._reconstruct_path(came_from, source, destination)
            return reconstructed_path
        else:
            raise NoRoutesLeft()

    def _sort_routes(self, routes: List[Route]) -> List[Route]:
        raise NotImplementedError

    def get_routes(self, source: KT, destination: KT) -> List[Route]:
        routes = []
        exclude_flights = []

        while True:
            try:
                result = self._search(source, destination, exclude_flights=exclude_flights)
            except (NoRoutesLeft, WrongRoute):
                break
            else:
                routes.append(result)
                exclude_flights += result

        filtered_routes = [
            route for route in [Route(tuple(flights)) for flights in routes]
            if route.arrival - route.departure <= timedelta(days=1)
        ]
        sorted_routes = self._sort_routes(filtered_routes)
        return sorted_routes


class DurationBasedGraph(AirportsGraph):
    @staticmethod
    def get_priority_value(obj: Flight) -> Any:
        return obj.duration

    def _sort_routes(self, routes: List[Route]) -> List[Route]:
        return sorted(routes, key=lambda r: (r.departure, r.total_duration), reverse=self.reverse)


class PriceBasedGraph(AirportsGraph):
    @staticmethod
    def get_priority_value(obj: Flight) -> Any:
        return float(obj.price.amount)

    def _sort_routes(self, routes: List[Route]) -> List[Route]:
        return sorted(routes, key=lambda r: r.total_price, reverse=self.reverse)
