from dataclasses import dataclass
from typing import Optional, TypedDict


@dataclass
class MainImage:
    url: str


@dataclass
class Street:
    name: str


@dataclass
class Address:
    house_number: Optional[str]
    street: Street


@dataclass
class Attributes:
    HOUSE_TYPE: list[str]
    FLOOR: int
    TOTAL_FLOOR: int
    ON_LAST_FLOOR: bool


@dataclass
class City24:
    main_image: MainImage
    date_published: str
    latitude: float
    longitude: float
    price: str
    property_size: str
    address: Address
    district: str
    city_name: str
    room_count: int
    district_name: str  # like Purvciems, Centrs, etc.
    attributes: Attributes
