import xml.etree.ElementTree as ET
from typing import List

from data_classes import Flight
from serializers import FlightSerializer


class FlightParser:
    def __init__(self, xml_data: List[str]):
        self.xml_data = xml_data
        self.serializer = FlightSerializer()

    def parse(self) -> List[Flight]:
        all_flights = []

        for xml in self.xml_data:
            raw_flights = ET.ElementTree(ET.fromstring(xml))

            for flight_group in raw_flights.iter('Flights'):
                pricing = flight_group.find('Pricing')

                if pricing:
                    currency = pricing.attrib['currency']
                    price = pricing.findtext('ServiceCharges[@ChargeType="TotalAmount"]')

                    for raw_flight in flight_group.iter('Flight'):
                        flight_data = self.serializer.dump({
                            **{attr.tag: attr.text for attr in raw_flight},
                            'price': float(price),
                            'currency': currency,
                        })
                        all_flights.append(Flight(**flight_data))

        return all_flights
