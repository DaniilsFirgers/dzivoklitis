import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo
from fake_useragent import UserAgent
from geopy.geocoders import Photon

from scraper.database.models import Price
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
    """Try to parse a string to an integer, return 0 if it fails"""
    try:
        return int(value)
    except ValueError as e:
        logger.error(f"Error parsing int: {e}")
        return 0


def try_parse_float(value: str) -> float:
    """Try to parse a string to a float, return 0.0 if it fails."""
    try:
        return float(value)
    except ValueError as e:
        logger.error(f"Error parsing float: {e}")
        return 0.0


def get_start_of_day() -> int:
    """Get the start of the current day in Unix timestamp."""
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


def find_flat_price(curr_price: int, prev_prices: List[Price]) -> Optional[Price]:
    """Finds the price object from the list of previous prices that matches the current price."""
    price_dict = {
        price.price: price for price in prev_prices}
    return price_dict.get(curr_price)


def valid_date_published(date_published_str: str) -> bool:
    """Check if date pubklished is after start of the day in EET"""

    now = datetime.now(ZoneInfo("Europe/Riga"))
    start_of_day = datetime(now.year, now.month, now.day,
                            0, 0, 0, tzinfo=ZoneInfo("Europe/Riga"))
    date_published = datetime.fromisoformat(date_published_str)

    return date_published >= start_of_day


def convert_dt_to_utc(dt_str: str) -> datetime:
    """Convert datetime string to UTC"""
    dt = datetime.fromisoformat(dt_str)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc
