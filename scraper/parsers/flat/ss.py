from datetime import datetime
import re
from typing import Dict
from zoneinfo import ZoneInfo

from scraper.utils.config import Source
from scraper.parsers.flat.base import Flat
from scraper.schemas.shared import DealType
from scraper.utils.meta import try_parse_float, try_parse_int


class SS_Flat(Flat):
    def __init__(self, url: str, district_name: str, raw_info: list[str], deal_type: DealType, city: str):
        super().__init__(url=url, district=district_name,
                         source=Source.SS, deal_type=deal_type.value)
        self.raw_info = raw_info
        self.city = city

    def create(self, unified_flat_series: Dict[str, str]):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price = self.get_price()
        self.price_per_m2 = try_parse_float(
            re.sub(r"[^\d.]", "", self.raw_info[5]))
        self.rooms = self.get_rooms()
        self.street = self.get_street()
        self.area = try_parse_float(self.raw_info[2], 2)
        self.floor, self.floors_total = self.get_floors(self.raw_info[3])
        self.series = unified_flat_series[self.raw_info[4]]
        self.id = self.create_id()
        self.created_at = datetime.now().astimezone(ZoneInfo("UTC"))

    def get_price(self) -> int:
        if self.deal_type == DealType.RENT.value:
            return try_parse_int(re.sub(r"[^\d]", "", self.raw_info[6]))
        return try_parse_int(re.sub(r"[^\d.]", "", self.raw_info[6]))

    def get_rooms(self) -> int:
        rooms = try_parse_int(self.raw_info[1])
        if rooms == 0 or rooms is None:
            raise ValueError("Rooms is 0 or None")
        return rooms

    def get_street(self) -> str:
        street = re.sub(r'\b[A-Za-z]{1,7}\.\s*', '', self.raw_info[0]).strip()
        return street

    def get_floors(self, floors: str) -> tuple[int, int] | tuple[None, None]:
        actual_floor_str, last_floor_str = floors.split("/")
        actual_floor = int(actual_floor_str)
        floors_total = int(last_floor_str)
        # sometimes people write floors_total/actual_floor
        if actual_floor > floors_total:
            return floors_total, actual_floor
        return actual_floor, floors_total
