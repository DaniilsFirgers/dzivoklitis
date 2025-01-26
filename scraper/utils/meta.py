

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
