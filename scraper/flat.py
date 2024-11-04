import re


class Flat:
    def __init__(self, id: str, link: str, district: str):
        self.id = id
        self.link = link
        self.district = district

    def add_info(self, raw_info: list[str]):
        if len(raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.street = raw_info[0]
        self.rooms = int(raw_info[1])
        self.m2 = float(raw_info[2])
        self.floor = raw_info[3]
        self.series = raw_info[4]
        self.price_per_m2 = int(re.sub(r"[^\d]", "", raw_info[5]))
        self.full_price = int(re.sub(r"[^\d]", "", raw_info[6]))
