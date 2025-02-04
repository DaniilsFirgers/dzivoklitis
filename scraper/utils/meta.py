

from datetime import datetime, timezone
from geopy.geocoders import Nominatim
import re

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


def get_coordinates(city: str, street: str) -> Coordinates | None:
    geolocator = Nominatim(user_agent="flats_scraper")
    # Remove sequences of letters followed by a dot (e.g., "J.", "pr.")
    # It helps to get better results
    cleaned_street = re.sub(r'\b[A-Za-z]{1,7}\.\s*', '', street)
    try:
        location = geolocator.geocode({
            "street": cleaned_street,
            "city": city,
            "country": "Latvia"
        })

        if location is None:
            logger.warning(
                f"Could not find coordinates for {street} in {city}")
            return None

        return Coordinates(location.latitude, location.longitude)
    except Exception as e:
        logger.error(e)
        return None
