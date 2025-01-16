import re
from scraper.config import District
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from scraper.utils.meta import try_parse_float, try_parse_int


class Source(Enum):
    SS = "ss"
    MM = "mm"
    CITY_24 = "city24"


@dataclass
class Flat():
    id: str
    link: str
    district: str
    source: Source
    district_info: Optional[District] = field(default=None)
    price_per_m2: Optional[float] = field(default=None)
    rooms: Optional[int] = field(default=None)
    street: Optional[str] = field(default=None)
    area: Optional[float] = field(default=None)
    floor: Optional[int] = field(default=None)
    last_floor: Optional[int] = field(default=None)
    series: Optional[str] = field(default=None)
    full_price: Optional[int] = field(default=None)

    def create(self):
        raise NotImplementedError("Method not implemented")

    def validate(self):
        if not self.district_info:
            raise ValueError("District info is not set")
        raise NotImplementedError("Method not implemented")

    @classmethod
    def from_sql_row(cls, *row):
        """
        Creates a Flat object from an SQL row.
        Maps row values to class attributes in order.
        """

        if (len(row) != 13):
            raise ValueError("Incorrect number of elements in row")

        return cls(
            id=row[0],
            source=row[1],
            link=row[2],
            district=row[3],
            street=row[4],
            rooms=row[5],
            last_floor=row[6],
            floor=row[7],
            price_per_m2=row[8],
            area=row[9],
            series=row[10],
            full_price=float(row[9]) * row[8]
        )


class SS_Flat(Flat):
    def __init__(self, id: str, link: str, district_info: District, raw_info: list[str]):
        super().__init__(id, link, district_info.name, Source.SS, district_info)
        self.raw_info = raw_info

    def create(self):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price_per_m2 = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[5]))
        self.rooms = try_parse_int(self.raw_info[1])
        self.street = self.raw_info[0]
        self.area = try_parse_float(self.raw_info[2])
        floors = self.parse_floors(self.raw_info[3])
        self.floor, self.last_floor = floors
        self.series = self.raw_info[4]
        self.full_price = self.area * float(self.price_per_m2)

    def validate(self):
        if (self.price_per_m2 > self.district_info.price_per_m2):
            raise ValueError("Price per m2 is higher than the limit")
        if (self.price_per_m2 < self.district_info.min_price_per_m2):
            raise ValueError("Price per m2 is lower than the limit")
        if (self.rooms != self.district_info.rooms):
            raise ValueError("Rooms do not match the settings")
        if (self.area < self.district_info.min_m2):
            raise ValueError("Area is less than the limit")
        if (self.floor < self.district_info.min_floor):
            raise ValueError("Floor is lower than the limit")
        if (self.last_floor == None or self.floor == None):
            raise ValueError("Could not parse floors")
        if (self.last_floor == self.floor and not self.district_info.last_floor):
            raise ValueError("Last floor is not allowed")
        if (self.last_floor < self.floor):
            raise ValueError("Last floor is lower than the floor")

    def parse_floors(self, floors: str) -> tuple[int, int] | tuple[None, None]:
        try:
            actual_floor_str, last_floor_str = floors.split("/")
            actual_floor = int(actual_floor_str)
            last_floor = int(last_floor_str)
            return actual_floor, last_floor
        except ValueError:
            return None, None
        except Exception:
            return None, None
