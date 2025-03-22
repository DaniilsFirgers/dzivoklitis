from typing import Dict
from scraper.parsers.base import UNKNOWN
from scraper.parsers.flat.base import Flat
from scraper.schemas.city_24 import Flat as City24Flat
from scraper.utils.config import Source
from scraper.schemas.shared import Coordinates, DealType
from scraper.utils.meta import convert_dt_to_utc, try_parse_float, try_parse_int


class City24_Flat(Flat):
    def __init__(self, district_name: str,  deal_type: DealType, flat: City24Flat, city: str):
        super().__init__(url="", district=district_name,
                         source=Source.CITY_24, deal_type=deal_type.value)
        self.flat = flat
        self.city = city

    def create(self, unified_flat_series: Dict[str, str]):
        self.url = self.format_url(self.flat["friendly_id"])
        self.price_per_m2 = self.flat["price_per_unit"]
        self.area = try_parse_float(self.flat["property_size"])
        self.price = try_parse_float((self.price_per_m2 * self.area))
        self.rooms = self.flat["room_count"]
        self.street = self.get_street_name()
        self.floor, self.floors_total = self.get_floors()
        self.series = self.get_series_type(unified_flat_series)
        self.id = self.create_id()
        self.add_coordinates(Coordinates(
            latitude=self.flat["latitude"], longitude=self.flat["longitude"]))
        self.created_at = convert_dt_to_utc(self.flat["date_published"])

    def get_floors(self) -> tuple[int, int]:
        floor = self.flat["attributes"]["FLOOR"]
        floors_total = self.flat["attributes"]["TOTAL_FLOORS"]

        # handle different cases :)
        if floor is None and floors_total is None:
            return None, None

        if floor is None:
            return floors_total, floors_total

        if floors_total is None:
            return floor, floor

        if floor > floors_total:
            return floors_total, floor

        return floor, floors_total

    def get_street_name(self) -> str:
        if self.flat["address"].get("house_number") is not None:
            return f'{self.flat["address"]["street_name"] or UNKNOWN} {self.flat["address"]["house_number"]}'
        return self.flat["address"]["street_name"] or UNKNOWN

    def get_series_type(self, unified_flat_series: Dict[str, str]) -> str:
        if self.flat["attributes"].get("HOUSE_TYPE") is None or len(self.flat["attributes"]["HOUSE_TYPE"]) <= 0:
            return UNKNOWN

        if self.flat["attributes"]["HOUSE_TYPE"][0] in unified_flat_series:
            return unified_flat_series[self.flat["attributes"]["HOUSE_TYPE"][0]]

        return UNKNOWN

    def format_img_url(self) -> str:
        url = self.flat["main_image"]["url"]
        return url.replace("{fmt:em}", "14")

    def format_url(self, id: str) -> str:
        if self.deal_type == DealType.RENT:
            return f"https://www.city24.lv/real-estate/apartments-for-rent/riga/{id}"

        return f"https://www.city24.lv/real-estate/apartments-for-sale/riga/{id}"
