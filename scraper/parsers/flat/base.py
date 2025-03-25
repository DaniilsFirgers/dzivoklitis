import hashlib
import pyvips
import aiohttp
from zoneinfo import ZoneInfo
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from scraper.utils.config import Source
from fake_useragent import UserAgent

from scraper.parsers.base import UNKNOWN
from scraper.schemas.shared import Coordinates
from scraper.utils.logger import logger
from scraper.database.models.flat import Flat as FlatORM
from scraper.database.models.price import Price


@dataclass
class Flat():
    url: str
    district: str
    source: Source
    deal_type: str
    id: Optional[str] = None
    price: Optional[int] = None
    rooms: Optional[int] = None
    city: Optional[str] = None
    street: Optional[str] = UNKNOWN
    area: Optional[float] = None
    floor: Optional[int] = None
    floors_total: Optional[int] = None
    series: Optional[str] = None
    price_per_m2: Optional[float] = None
    latitude: Optional[float] = 0
    longitude: Optional[float] = 0
    image_data: Optional[bytes] = b""
    created_at: Optional[datetime] = datetime.now().astimezone(ZoneInfo("UTC"))

    def create(self):
        pass

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
            logger.error(f"Error downloading image: {e} - {img_url}")
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
        id = f"{self.source.value}-{self.deal_type}-{self.district}-{self.street}-{self.series}-{self.rooms}-{self.area}-{self.floor}-{self.floors_total}"
        return hashlib.md5(id.encode()).hexdigest()

    def to_orm(self) -> FlatORM:
        return FlatORM(
            flat_id=self.id,
            source=self.source.value,
            deal_type=self.deal_type,
            created_at=self.created_at,
            url=self.url,
            city=self.city,
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
            city=flat.city,
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
