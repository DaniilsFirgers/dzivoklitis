import hashlib
import io
import re
from scraper.config import District, Source
from dataclasses import dataclass, field
from typing import Optional
from scraper.utils.meta import try_parse_float, try_parse_int
import requests
from PIL import Image


@dataclass
class Coordinates:
    latitude: float
    longitude: float


@dataclass
class Flat():
    url: str
    district: str
    source: Source
    deal_type: str = field(default=None)
    id: str = field(default=None)
    price: Optional[int] = field(default=None)
    rooms: Optional[int] = field(default=None)
    street: Optional[str] = field(default=None)
    area: Optional[float] = field(default=None)
    floor: Optional[int] = field(default=None)
    floors_total: Optional[int] = field(default=None)
    series: Optional[str] = field(default=None)
    price_per_m2: Optional[int] = field(default=None)
    latitude: Optional[float] = field(default=None)
    longitude: Optional[float] = field(default=None)
    image_data: Optional[bytes] = field(default=None)

    def __post_init__(self):
        self.create()

    def create(self):
        pass

    def validate(self):
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
            f"{self.source.value}-{self.deal_type}-{self.district}-{self.street}-{self.series}-{self.rooms}-{self.area}-{self.floor}-{self.floors_total}".encode()).hexdigest()

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
            deal_type=row[2],
            url=row[3],
            district=row[4],
            street=row[5],
            rooms=row[6],
            floors_total=row[7],
            floor=row[8],
            area=row[9],
            series=row[10],
            price=row[14],
            price_per_m2=int(row[14] / row[9]),
            latitude=row[11],
            longitude=row[12],
            image_data=row[13]
        )


class SS_Flat(Flat):
    def __init__(self, url: str, district_name: str, raw_info: list[str], deal_type: str, img_url: str | None):
        self.raw_info = raw_info
        self.img_url = img_url
        super().__init__(url=url, district=district_name,
                         source=Source.SS, deal_type=deal_type)

    def create(self):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[6]))
        self.price_per_m2 = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[5]))
        self.rooms = try_parse_int(self.raw_info[1])
        self.street = self.raw_info[0]
        self.area = try_parse_float(self.raw_info[2])
        floors = self.parse_floors(self.raw_info[3])
        self.floor, self.floors_total = floors
        self.series = self.raw_info[4]
        self.id = self.create_id()

    def validate(self, district_info: District):
        if (self.price / self.area > district_info.max_price_per_m2):
            raise ValueError("Price per m2 is higher than the limit")
        if (self.price / self.area < district_info.min_price_per_m2):
            raise ValueError("Price per m2 is lower than the limit")
        if (self.rooms != district_info.rooms):
            raise ValueError("Rooms do not match the settings")
        if (self.area < district_info.min_m2):
            raise ValueError("Area is less than the limit")
        if (self.floor < district_info.min_floor):
            raise ValueError("Floor is lower than the limit")
        if (self.floors_total == None or self.floor == None):
            raise ValueError("Could not parse floors")
        if (self.floors_total == self.floor and district_info.skip_last_floor):
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

        image_file = io.BytesIO(response.content)
        image = Image.open(image_file)
        max_size = (303, 230)

        image.thumbnail(max_size, Image.LANCZOS)  # Maintains aspect ratio
        resized_image_file = io.BytesIO()
        image.save(resized_image_file, format="JPEG")

        resized_image_file.seek(0)
        self.image_data = resized_image_file.getvalue()
