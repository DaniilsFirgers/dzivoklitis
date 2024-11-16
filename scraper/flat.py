import re

from scraper.config import District


class Flat:
    def __init__(self, id: str, link: str, district: str, **kwargs):
        self.id = id
        self.link = link
        self.district = district

        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            "id": self.id,
            "link": self.link,
            "district": self.district,
            "price_per_m2": self.price_per_m2,
            "rooms": self.rooms,
            "street": self.street,
            "m2": self.m2,
            "floor": self.floor,
            "last_floor": self.last_floor,
            "series": self.series,
            "full_price": self.full_price
        }

    def add_info(self, raw_info: list[str], settings: District):
        if len(raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")

        self.price_per_m2 = self.try_parse_int(
            re.sub(r"[^\d]", "", raw_info[5]))
        if (settings.price_per_m2 < self.price_per_m2):
            raise ValueError("Price per m2 is higher than the limit")
        if (self.price_per_m2 < settings.min_price_per_m2):
            raise ValueError("Price per m2 is lower than the limit")
        self.rooms = self.try_parse_int(raw_info[1])
        if (self.rooms != settings.rooms):
            raise ValueError("Rooms do not match the settings")
        self.street = raw_info[0]
        self.m2 = self.try_parse_float(raw_info[2])
        if (self.m2 < settings.min_m2):
            raise ValueError("M2 is lower than the limit")
        floors = self.parse_floors(raw_info[3])
        if floors is None:
            raise ValueError("Could not parse floors")
        self.floor, self.last_floor = floors
        if (self.floor < settings.min_floor):
            raise ValueError("Floor is lower than the limit")
        if (self.last_floor == self.floor and not settings.last_floor):
            raise ValueError("Last floor is not allowed")
        self.series = raw_info[4]
        self.full_price = self.try_parse_int(re.sub(r"[^\d]", "", raw_info[6]))

    def try_parse_int(self, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            return 0

    def try_parse_float(self, value: str) -> float:
        try:
            return float(value)
        except ValueError:
            return 0.0

    def parse_floors(self, floors: str) -> tuple[int, int] | None:
        try:
            actual_floor_str, last_floor_str = floors.split("/")
            actual_floor = int(actual_floor_str)
            last_floor = int(last_floor_str)
            return actual_floor, last_floor
        except ValueError:
            return None
        except Exception:
            return None
