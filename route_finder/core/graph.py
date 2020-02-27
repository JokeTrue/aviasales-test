import abc
from collections import defaultdict
from queue import PriorityQueue
from typing import List, Union, Dict, Any

from data_classes import Flight, Route
from exceptions import NoRoutesLeft
from geo import distance, get_airport_coordinates


class SimpleGraph(abc.ABC):
    def __init__(self, edges):
        self.edges = edges

    def neighbors(self, key) -> List:
        return self.edges[key]

    def heuristic(self, from_node, to_node) -> Union[int, float]:
        raise NotImplementedError

    def _search(self, source: str, destination: str) -> List[Flight]:
        raise NotImplementedError


class AirportsGraph(SimpleGraph):
    def __init__(self, edges, airports: Dict, reverse=False):
        self.reverse = reverse
        self.airports_data = airports

        flights = defaultdict(set)
        for flight in edges:
            flights[flight.source].add(flight)

        self.edges = flights

    def heuristic(self, from_node, to_node) -> Union[int, float]:
        from_coords = get_airport_coordinates(self.airports_data, from_node)
        to_coords = get_airport_coordinates(self.airports_data, to_node)

        return distance(from_coords, to_coords)

    @staticmethod
    def get_priority_value(obj: Flight):
        raise NotImplementedError

    @staticmethod
    def _get_best_options(flights: List[Flight], exclude_flights: List[Flight] = None) -> List[Flight]:
        if exclude_flights is None:
            exclude_flights = []

        best_flight_options = {}
        filtered_flights = [item for item in flights if item not in exclude_flights]

        for flight in filtered_flights:
            if (
                    flight.destination not in best_flight_options or
                    flight.duration < best_flight_options[flight.destination].duration
            ):
                best_flight_options[flight.destination] = flight

        return list(best_flight_options.values())

    @staticmethod
    def _reconstruct_path(came_from: Dict[str, Any], source: str, destination: str) -> List[Flight]:
        flight = came_from[destination]
        path = [flight]

        while flight.source != source:
            flight = came_from[flight.source]
            path.insert(0, flight)

        return path

    def _search(self, source: str, destination: str, exclude_flights=None) -> List[Flight]:
        q = PriorityQueue()
        q.put((0, source))

        came_from = {}
        cost_so_far = {source: 0}

        while not q.empty():
            priority, current_airport = q.get()

            if current_airport == destination:
                break

            best_options = self._get_best_options(self.neighbors(current_airport), exclude_flights)
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

    def sort_routes(self, routes: List[Route]) -> List[Route]:
        raise NotImplementedError

    def get_routes(self, source: str, destination: str):
        routes = []
        exclude_flights = []

        while True:
            try:
                result = self._search(source, destination, exclude_flights=exclude_flights)
            except NoRoutesLeft:
                break

            routes.append(result)
            exclude_flights += result

        unique_routes = [Route(flights) for flights in set(tuple(flights) for flights in routes)]
        sorted_routes = self.sort_routes(unique_routes)
        return sorted_routes


class DurationBasedGraph(AirportsGraph):
    @staticmethod
    def get_priority_value(obj: Flight):
        return obj.duration

    def sort_routes(self, routes: List[Route]) -> List[Route]:
        return sorted(routes, key=lambda r: (r.departure, r.total_duration), reverse=self.reverse)


class PriceBasedGraph(AirportsGraph):
    @staticmethod
    def get_priority_value(obj: Flight):
        return float(obj.price.amount)

    def sort_routes(self, routes: List[Route]) -> List[Route]:
        return sorted(routes, key=lambda r: r.total_price, reverse=self.reverse)
