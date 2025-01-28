

from typing import Optional, TypedDict


class MainImage(TypedDict):
    url: str


class Street(TypedDict):
    name: str


class Adress(TypedDict):
    house_number: Optional[str]
    street: Street


class Attributes(TypedDict):
    HOUSE_TYPE: list[str]
    FLOOR: int
    TOTAL_FLOOR: int
    ON_LAST_FLOOR: bool


class City24(TypedDict):
    main_image: MainImage
    date_published: str
    latitude: float
    longitude: float
    price: str
    property_size: str
    adress: Adress
    district: str
    city_name: str
    room_count: int
    district_name: str  # like Purvciems, Centrs, etc.
    attributes: Attributes
