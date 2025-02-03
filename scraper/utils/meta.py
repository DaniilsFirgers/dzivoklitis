

from datetime import datetime, timezone


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
