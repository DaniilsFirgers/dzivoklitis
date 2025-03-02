import hashlib
import re
import pyvips
import aiohttp

from scraper.config import District, Source
from dataclasses import dataclass
from typing import Dict, Optional
from scraper.parsers.base import UNKNOWN_DISTRICT
from scraper.schemas.city_24 import Flat as City24Flat
from scraper.schemas.shared import Coordinates, DealType
from scraper.utils.logger import logger
from scraper.utils.meta import get_coordinates, try_parse_float, try_parse_int
from fake_useragent import UserAgent
from scraper.database.models import Flat as FlatORM, Price
from scraper.schemas.pp import FilterValue, Flat as PpFlat, PriceType


@dataclass
class Flat():
    url: str
    district: str
    source: Source
    deal_type: str
    id: Optional[str] = None
    price: Optional[int] = None
    rooms: Optional[int] = None
    street: Optional[str] = None
    area: Optional[float] = None
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    series: Optional[str] = None
    price_per_m2: Optional[int] = None
    latitude: Optional[float] = 0
    longitude: Optional[float] = 0
    image_data: Optional[bytes] = b""

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
                img_data = await response.read()
                image = pyvips.Image.new_from_buffer(img_data, "")

                # Automatically keeps aspect ratio
                image = image.thumbnail_image(303)
                resized_image_file = image.write_to_buffer(
                    ".jpg")

                return resized_image_file
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

    def to_orm(self) -> FlatORM:
        return FlatORM(
            flat_id=self.id,
            source=self.source.value,
            deal_type=self.deal_type,
            url=self.url,
            district=self.district,
            street=self.street,
            rooms=self.rooms,
            floors_total=self.floors_total,
            floor=self.floor,
            area=self.area,
            series=self.series,
            location=f"POINT({self.longitude} {self.latitude})",
            image_data=self.image_data,
        )

    @staticmethod
    def from_orm(flat: FlatORM):
        last_update: Price = max(
            flat.prices, key=lambda x: x.updated_at, default=None)
        return Flat(
            url=flat.url,
            district=flat.district,
            source=Source(flat.source),
            deal_type=flat.deal_type,
            id=flat.flat_id,
            price=last_update.price if last_update else 0,
            rooms=flat.rooms,
            street=flat.street,
            area=flat.area,
            floor=flat.floor,
            floors_total=flat.floors_total,
            series=flat.series,
            price_per_m2=int(last_update.price /
                             flat.area) if last_update else 0,
            latitude=0,  # currently we dont care about coordinates
            longitude=0,  # currently we dont care about coordinates
            image_data=flat.image_data
        )


class SS_Flat(Flat):
    def __init__(self, url: str, district_name: str, raw_info: list[str], deal_type: DealType):
        super().__init__(url=url, district=district_name,
                         source=Source.SS, deal_type=deal_type)
        self.raw_info = raw_info

    def create(self, unified_flat_series: Dict[str, str]):
        if len(self.raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.price = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[6]))
        self.price_per_m2 = try_parse_int(
            re.sub(r"[^\d]", "", self.raw_info[5]))
        self.rooms = try_parse_int(self.raw_info[1])
        cleaned_street = re.sub(r'\b[A-Za-z]{1,7}\.\s*', '', self.raw_info[0])
        self.street = f"{cleaned_street} iela"
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
    def __init__(self, district_name: str,  deal_type: DealType, flat: City24Flat):
        super().__init__(url="", district=district_name,
                         source=Source.CITY_24, deal_type=deal_type)
        self.flat = flat

    def create(self, unified_flat_series: Dict[str, str]):
        self.url = self.format_url(self.flat["friendly_id"])
        self.price_per_m2 = self.flat["price_per_unit"]
        self.area = try_parse_float(self.flat["property_size"])
        self.price = try_parse_int((self.price_per_m2 * self.area))
        self.rooms = self.flat["room_count"]
        self.street = self.get_street_name()
        self.floor = self.flat["attributes"]["FLOOR"]
        self.floors_total = self.flat["attributes"]["TOTAL_FLOORS"]
        self.series = self.get_series_type(unified_flat_series)
        self.id = self.create_id()
        self.add_coordinates(Coordinates(
            latitude=self.flat["latitude"], longitude=self.flat["longitude"]))

    def get_street_name(self) -> str:
        if self.flat["address"].get("house_number") is not None:
            return f'{self.flat["address"]["street_name"]} {self.flat["address"]["house_number"]}'
        return self.flat["address"]["street_name"]

    def get_series_type(self, unified_flat_series: Dict[str, str]) -> str:
        if self.flat["attributes"].get("HOUSE_TYPE") is None or len(self.flat["attributes"]["HOUSE_TYPE"]) <= 0:
            return UNKNOWN_DISTRICT

        if self.flat["attributes"]["HOUSE_TYPE"][0] in unified_flat_series:
            return unified_flat_series[self.flat["attributes"]["HOUSE_TYPE"][0]]

        return UNKNOWN_DISTRICT

    def format_img_url(self) -> str:
        url = self.flat["main_image"]["url"]
        return url.replace("{fmt:em}", "14")

    def format_url(self, id: str) -> str:
        if self.deal_type == DealType.RENT:
            return f"https://www.city24.lv/real-estate/apartments-for-rent/riga/{id}"

        return f"https://www.city24.lv/real-estate/apartments-for-sale/riga/{id}"


PP_FILTER_MAP: Dict[str, FilterValue] = {
    "area": {"id": 123, "default": 10},
    "rooms": {"id": 121, "default": 1},
    "floor": {"id": 125, "default": 1},
    "floors_total": {"id": 139, "default": 1},
    "series": {"id": 127, "default": UNKNOWN_DISTRICT},
}


class PP_Flat(Flat):
    def __init__(self, district_name: str,  deal_type: str, flat: PpFlat):
        super().__init__(url="", district=district_name,
                         source=Source.PP, deal_type=deal_type)
        self.flat = flat

    def create(self, unified_flat_series: Dict[str, str]):
        self.url = self.flat["frontUrl"]
        self.price = self.get_price(PriceType.SELL_FULL)
        self.price_per_m2 = self.get_price(PriceType.SELL_SQUARE)
        self.area = self.get_text_attribute(PP_FILTER_MAP["area"])
        self.rooms = self.get_text_attribute(PP_FILTER_MAP["rooms"])
        self.street = self.flat["publicLocation"]["address"]
        self.floor = self.get_text_attribute(PP_FILTER_MAP["floor"])
        self.floors_total = self.get_text_attribute(
            PP_FILTER_MAP["floors_total"])
        self.series = self.get_series_type(unified_flat_series)
        self.id = self.create_id()
        self.add_coordinates(Coordinates(
            latitude=self.flat["publicLocation"]["coordinateY"], longitude=self.flat["publicLocation"]["coordinateX"]))

    def get_price(self, priceType: PriceType) -> int:
        """Get the price of the flat"""
        prices = self.flat["prices"]
        targetPrice = next(
            (price for price in prices if price["priceType"]["id"] == priceType.value), None)
        if targetPrice is None:
            return 0
        print("qwe", targetPrice["value"])
        return try_parse_float(targetPrice["value"])

    def get_text_attribute(self, filter_value: FilterValue) -> int:
        """Get attributes from the flat filters"""
        attr = next(
            (attr for attr in self.flat["adFilterValues"] if attr["filter"]["id"] == filter_value["id"]), None)
        if attr is None:
            return filter_value["default"]
        return try_parse_int(attr["textValue"])

    def get_series_type(self, unified_flat_series: Dict[str, str]) -> str:
        attr = next(
            (attr for attr in self.flat["adFilterValues"] if attr["filter"]["id"] == PP_FILTER_MAP["series"]["id"]), None)
        if attr is None:
            return PP_FILTER_MAP["series"]["default"]

        if str(attr["value"]["id"]) in unified_flat_series:
            return unified_flat_series[str(attr["value"]["id"])]
        return UNKNOWN_DISTRICT

    def format_img_url(self) -> str:
        extension = self.flat["thumbnail"]["extension"]
        storage_id = self.flat["thumbnail"]["storageId"]
        return f"https://img.pp.lv/storage/{storage_id[0:2]}/{storage_id[2:4]}/{storage_id}/32.{extension}"
