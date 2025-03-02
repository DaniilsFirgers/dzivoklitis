from typing import TypedDict, Optional


class MainImageDict(TypedDict):
    url: str


class AddressDict(TypedDict, total=False):  # `total=False` makes fields optional
    house_number: Optional[str]
    street_name: str
    district_name: str


class AttributesDict(TypedDict, total=False):
    HOUSE_TYPE: Optional[list[str]]
    FLOOR: int
    TOTAL_FLOORS: int
    ON_LAST_FLOOR: bool


class Flat(TypedDict, total=False):
    main_image: MainImageDict
    date_published: str
    latitude: float
    longitude: float
    price: str
    price_per_unit: float
    property_size: str
    friendly_id: str
    address: AddressDict
    room_count: int
    attributes: AttributesDict
