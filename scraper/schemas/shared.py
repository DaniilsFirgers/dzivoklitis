from dataclasses import dataclass
from enum import Enum


@dataclass
class Coordinates:
    latitude: float
    longitude: float


class DealType(Enum):
    SELL = "Pārdod"
    RENT = "Izīrē"
