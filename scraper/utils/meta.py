

import asyncio
from datetime import datetime, timezone
from typing import Optional
from fake_useragent import UserAgent
from geopy.geocoders import Photon

from scraper.flat import Coordinates
from scraper.utils.logger import logger


class SingletonMeta(type):
    """
    A metaclass for creating singleton classes.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def try_parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def try_parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def get_start_of_day() -> int:
    now = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)

    start_of_day = datetime(now.year, now.month, now.day)

    return int(start_of_day.timestamp())


async def async_geocode(geolocator: Photon, full_address: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, geolocator.geocode, full_address)


async def get_coordinates(city: str, street: str) -> Optional[Coordinates]:
    ua = UserAgent()
    geolocator = Photon(user_agent=ua.random)

    # Prepare the query
    full_address = f"{street}, {city}, Latvija"
    print(full_address)
    try:
        # Call async_geocode which uses the ThreadPoolExecutor
        location = await async_geocode(geolocator, full_address)

        if location is None:
            logger.warning(
                f"Could not find coordinates for {street} in {city}")
            return None
        logger.info(
            f"Found coordinates for {street} in {city}: {location.latitude}, {location.longitude}")
        return Coordinates(location.latitude, location.longitude)

    except Exception as e:
        logger.error(f"Error during geocoding: {e}")
        return None
