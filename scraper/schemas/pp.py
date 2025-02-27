from typing import List, TypedDict


class AdFilter(TypedDict, total=False):
    id: int
    name: str


class AdFilterValue(TypedDict, total=False):
    textValue: int | str
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


class Flat(TypedDict, total=False):
    publicLocation: PublicLocation
    frontUrl: str
    adFilterValues: List[AdFilterValue]


class Content(TypedDict, total=False):
    data: List[Flat]


class City24ResFlatsDict(TypedDict, total=False):
    content: Content
    count: int
