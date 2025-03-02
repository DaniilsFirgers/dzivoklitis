from enum import Enum
from typing import List, TypedDict, Union


class AdFilter(TypedDict, total=False):
    id: int
    name: str


class FilterValue(TypedDict, total=False):
    id: int


class AdFilterValue(TypedDict, total=False):
    textValue: int | str
    value: FilterValue
    filter: AdFilter


class Parent(TypedDict, total=False):
    id: int
    name: str


class Region(TypedDict, total=False):
    id: int
    name: str
    parent: Parent


class PublicLocation(TypedDict, total=False):
    coordinateX: float
    coordinateY: float
    address: str
    region: Region


class PriceType(TypedDict):
    id: int
    name: str


class PriceHistory(TypedDict):
    value: str
    timestamp: str
    priceType: PriceType


class Price(TypedDict, total=False):
    value: str
    priceType: PriceType
    priceHistory: List[PriceHistory]


class Thumbnail(TypedDict):
    extension: str
    storageId: str


class Flat(TypedDict, total=False):
    publicLocation: PublicLocation
    frontUrl: str
    adFilterValues: List[AdFilterValue]
    prices: List[Price]
    publishDate: str
    thumbnail: Thumbnail


class Content(TypedDict, total=False):
    data: List[Flat]
    count: int


class City24ResFlatsDict(TypedDict, total=False):
    content: Content


class FilterValue(TypedDict):
    id: int
    default: Union[int, str]


class PriceType(Enum):
    SELL_FULL = 1
    SELL_SQUARE = 15
    RENT_FULL = 3
    RENT_SQUARE = 5
