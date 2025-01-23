import hashlib
import re
from scraper.config import District, Source
from dataclasses import dataclass, field
from typing import Optional
from scraper.utils.meta import try_parse_float, try_parse_int
import requests


@dataclass
class Coordinates:
    latitude: float
    longitude: float


@dataclass
class Flat():
    url: str
    district: str
    source: Source
    id: str = field(default=None)
    district_info: Optional[District] = field(default=None)
    price_per_m2: Optional[int] = field(default=None)
    rooms: Optional[int] = field(default=None)
    street: Optional[str] = field(default=None)
    area: Optional[float] = field(default=None)
    floor: Optional[int] = field(default=None)
    floors_total: Optional[int] = field(default=None)
    series: Optional[str] = field(default=None)
    full_price: Optional[int] = field(default=None)
    latitude: Optional[float] = field(default=None)
    longitude: Optional[float] = field(default=None)
    image_data: Optional[bytes] = field(default=None)

    def __post_init__(self):
        self.create()

    def create(self):
        pass

    def validate(self):
        if not self.district_info:
            raise ValueError("District info is not set")
        pass

    def add_coordinates(self, coordinates: Coordinates):
        self.latitude = coordinates.latitude
        self.longitude = coordinates.longitude

    def create_id(self):
        """Creates a unique id for the flat based on the following attributes:
            - source
            - district
            - street
            - series
            - rooms
            - area
            - floor 
            - floors_total
        This strategy is used because the id in the source website can change. Moreover, we want to track
        how the price changes for the same flat over time.
        For a more efficient storage, we hash the id with md5.
        """
        return hashlib.md5(
            f"{self.source.value}-{self.district}-{self.street}-{self.series}-{self.rooms}-{self.area}-{self.floor}-{self.floors_total}".encode()).hexdigest()

    @classmethod
    def from_sql_row(cls, *row):
        """
        Creates a Flat object from an SQL row.
        Maps row values to class attributes in order.
        """
        if (len(row) != 14):
            raise ValueError("Incorrect number of elements in row")

        return cls(
            id=row[0],
            source=row[1],
            url=row[2],
            district=row[3],
            street=row[4],
            rooms=row[5],
            floors_total=row[6],
            floor=row[7],
            area=row[8],
            series=row[9],
            full_price=int(row[13] * row[8]),
            price_per_m2=row[13],
            latitude=row[10],
            longitude=row[11],
            image_data=row[12]
        )


class SS_Flat(Flat):
    def __init__(self, url: str, district_info: District, raw_info: list[str], img_url: str | None):
        self.raw_info = raw_info
        self.img_url = img_url
        super().__init__(url=url, district=district_info.name,
                         source=Source.SS, district_info=district_info)

    def create(self):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price_per_m2 = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[5]))
        self.rooms = try_parse_int(self.raw_info[1])
        self.street = self.raw_info[0]
        self.area = try_parse_float(self.raw_info[2])
        floors = self.parse_floors(self.raw_info[3])
        self.floor, self.floors_total = floors
        self.series = self.raw_info[4]
        self.full_price = self.area * float(self.price_per_m2)
        self.id = self.create_id()

    def validate(self):
        if (self.price_per_m2 > self.district_info.max_price_per_m2):
            raise ValueError("Price per m2 is higher than the limit")
        if (self.price_per_m2 < self.district_info.min_price_per_m2):
            raise ValueError("Price per m2 is lower than the limit")
        if (self.rooms != self.district_info.rooms):
            raise ValueError("Rooms do not match the settings")
        if (self.area < self.district_info.min_m2):
            raise ValueError("Area is less than the limit")
        if (self.floor < self.district_info.min_floor):
            raise ValueError("Floor is lower than the limit")
        if (self.floors_total == None or self.floor == None):
            raise ValueError("Could not parse floors")
        if (self.floors_total == self.floor and not self.district_info.skip_last_floor):
            raise ValueError("Last floor is not allowed")
        if (self.floors_total < self.floor):
            raise ValueError("Last floor is lower than the floor")

    def parse_floors(self, floors: str) -> tuple[int, int] | tuple[None, None]:
        try:
            actual_floor_str, last_floor_str = floors.split("/")
            actual_floor = int(actual_floor_str)
            floors_total = int(last_floor_str)
            return actual_floor, floors_total
        except ValueError:
            return None, None
        except Exception:
            return None, None

    def load_img(self):
        if self.img_url is None:
            return
        response = requests.get(self.img_url)
        if response.status_code != 200:
            return
        self.image_data = response.content
