import hashlib
import io
import re

import aiohttp
from scraper.config import District, Source
from dataclasses import dataclass, field
from typing import Dict, Optional
from scraper.schemas.city_24 import City24ResFlatDict
from scraper.schemas.shared import Coordinates, DealType
from scraper.utils.logger import logger
from scraper.utils.meta import get_coordinates, try_parse_float, try_parse_int
from PIL import Image
from fake_useragent import UserAgent


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

    def create(self):
        pass

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

    async def download_img(self, img_url: str, session: aiohttp.ClientSession) -> bytes:
        if img_url is None:
            return None

        headers = {
            "User-Agent":  UserAgent().random,
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with session.get(img_url, headers=headers) as response:
                if response.status != 200:
                    print(
                        f"Failed to download image from {img_url} - {response.status}")
                    return None

                # Get image content and open it
                img_data = await response.read()  # Read the image asynchronously
                image_file = io.BytesIO(img_data)
                image = Image.open(image_file)

                # Resize image while maintaining aspect ratio
                max_size = (303, 230)
                image.thumbnail(max_size, Image.LANCZOS)

                # Save to BytesIO buffer
                resized_image_file = io.BytesIO()
                image.save(resized_image_file, format="JPEG")

                resized_image_file.seek(0)
                logger.info(f"Downloaded image from {img_url}")
                return resized_image_file.getvalue()
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

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
    def __init__(self, url: str, district_name: str, raw_info: list[str], deal_type: str):
        super().__init__(url=url, district=district_name,
                         source=Source.SS, deal_type=deal_type)
        self.raw_info = raw_info

    def create(self, img_url: str, unified_flat_series: Dict[str, str]):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[6]))
        self.price_per_m2 = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[5]))
        self.rooms = try_parse_int(self.raw_info[1])
        self.street = self.raw_info[0]
        self.area = try_parse_float(self.raw_info[2])
        self.floor, self.floors_total = self.parse_floors(self.raw_info[3])
        self.series = unified_flat_series[self.raw_info[4]]
        self.id = self.create_id()

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


class City24_Flat(Flat):
    def __init__(self,  district_name: str,  deal_type: str, flat: City24ResFlatDict):
        url = self.format_url(flat["friendly_id"])
        super().__init__(url=url, district=district_name,
                         source=Source.CITY_24, deal_type=deal_type)
        self.flat = flat

    def create(self, unified_flat_series: Dict[str, str]):
        self.price_per_m2 = self.flat["price_per_unit"]
        self.area = try_parse_float(self.flat["property_size"])
        self.price = try_parse_int((self.price_per_m2 * self.area))
        self.rooms = self.flat["room_count"]
        self.street = f'{self.flat["address"]["street_name"]} {self.flat["address"]["house_number"]}'
        self.floor = self.flat["attributes"]["FLOOR"]
        self.floors_total = self.flat["attributes"]["TOTAL_FLOORS"]
        self.series = self.get_series_type(unified_flat_series)
        img_url = self.format_img_url(self.flat["main_image"]["url"])
        self.id = self.create_id()
        self.add_coordinates(Coordinates(
            latitude=self.flat["latitude"], longitude=self.flat["longitude"]))
        self.image_data = self.download_img(img_url)

    def get_series_type(self, unified_flat_series: Dict[str, str]) -> str:
        if self.flat["attributes"].get("HOUSE_TYPE") is not None and len(self.flat["attributes"]["HOUSE_TYPE"]) > 0:
            return unified_flat_series[self.flat["attributes"]["HOUSE_TYPE"][0]]
        return "Nezināms"

    def format_img_url(self, url: str) -> str:
        return url.replace("{fmt:em}", "14")

    def format_url(self, id: str) -> str:
        # curently it is only Riga, but i want to make it universal
        if self.deal_type == DealType.RENT:
            return f"https://www.city24.lv/real-estate/apartments-for-rent/riga/{id}"

        return f"https://www.city24.lv/real-estate/apartments-for-sale/riga/{id}"
