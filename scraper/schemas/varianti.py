from typing import List, TypedDict


class Image(TypedDict):
    small: str
    original: str


class Object(TypedDict, total=False):
    area: float
    price: float
    price_per_m: float
    floor: int
    floors_count: int
    rooms_count: int
    flat_building_type: int
    date_create: int
    date_update: int


class Address(TypedDict):
    city_id: int
    street: str
    house: str
    street_id: int
    apartment: str


class Flat(TypedDict, total=False):
    valid_from: int
    id: int
    valid_till: int
    address_name: str
    address: Address
    latitude: float
    longitude: float
    deal_type: int
    category_type: int
    object: Object
    images: List[Image]


class Result(TypedDict, total=False):
    pages: int
    total: int
    list: List[Flat] | None


class VariantiRes(TypedDict, total=False):
    statusCode: str
    errorCodes: List[str]
    errorDescriptions: List[str]
    result: Result
