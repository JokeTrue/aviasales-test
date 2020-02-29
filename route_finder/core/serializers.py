import dataclasses
from datetime import datetime
from decimal import Decimal

from data_classes import Money
from marshmallow import Schema, fields, INCLUDE


class FlightSerializer(Schema):
    class Meta:
        unknown = INCLUDE

    carrier = fields.Str(attribute='Carrier')
    source = fields.Str(attribute='Source')
    destination = fields.Str(attribute='Destination')
    departure = fields.Method('get_departure')
    arrival = fields.Method('get_arrival')
    duration = fields.Method('get_duration')
    price = fields.Method('get_price')

    def get_duration(self, obj):
        return (self.get_arrival(obj) - self.get_departure(obj)).total_seconds()

    def get_departure(self, obj):
        return datetime.strptime(obj['DepartureTimeStamp'], '%Y-%m-%dT%H%M')

    def get_arrival(self, obj):
        return datetime.strptime(obj['ArrivalTimeStamp'], '%Y-%m-%dT%H%M')

    def get_price(self, obj):
        return Money(Decimal(obj['price']), obj['currency'])


class RouteSerializer(Schema):
    departure = fields.DateTime()
    arrival = fields.DateTime()
    total_price = fields.Float()
    total_duration = fields.Int()
    number_of_flights = fields.Int(attribute='number_of_flights')
    flights = fields.Method('get_flights')

    def get_flights(self, obj):
        return [dataclasses.asdict(f) for f in obj.flights]
