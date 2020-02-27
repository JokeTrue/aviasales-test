from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Tuple


@dataclass(frozen=True, eq=True)
class Flight:
    carrier: str
    source: str
    destination: str
    duration: int
    departure: datetime
    arrival: datetime
    price: float

    def __repr__(self):
        return f'<Flight {self.source}->{self.destination} duration={self.duration} price={str(self.price)}>'

    def __lt__(self, other):
        return self.duration < other.duration


@dataclass(eq=False, frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __str__(self):
        return f'{self.currency} {round(self.amount, 2)}'

    def __repr__(self):
        return f'<{self.currency} {round(self.amount, 2)}>'


@dataclass(frozen=True)
class Route:
    flights: Tuple[Flight]

    def __repr__(self):
        return f'<Route ' \
               f'flights={self.number_of_flights} ' \
               f'duration={self.total_duration} ' \
               f'price={self.total_price} ' \
               f'{self.departure}->{self.arrival}' \
               f'>'

    @property
    def total_duration(self):
        return sum(map(lambda f: f.duration, self.flights))

    @property
    def total_price(self):
        return round(sum(map(lambda f: f.price.amount, self.flights)), 2)

    @property
    def departure(self):
        return self.flights[0].departure

    @property
    def arrival(self):
        return self.flights[-1].arrival

    @property
    def number_of_flights(self):
        return len(self.flights)
