from typing import Dict

from scraper.parsers.base import UNKNOWN
from scraper.parsers.flat.base import Flat
from scraper.schemas.varianti import Flat as FlatSchema
from scraper.utils.config import Source
from scraper.schemas.shared import Coordinates, DealType
from scraper.utils.meta import convert_timestamp_to_utc, try_parse_int


class Varianti_Flat(Flat):
    def __init__(self, district_name: str,  deal_type: DealType, flat: FlatSchema, city: str):
        super().__init__(url=self.format_url(flat["id"]), district=district_name,
                         source=Source.VARIANTI, deal_type=deal_type.value)
        self.flat = flat
        self.city = city

    def create(self, internal_series: Dict[str, str]):
        self.price_per_m2 = self.get_object_num("price_per_m")
        self.area = round(self.get_object_num("area"), 1)
        self.price = self.get_object_num("price")
        self.rooms = self.get_object_num("rooms_count")
        self.street = self.get_street_name()
        self.floor = self.get_object_num("floor")
        self.floors_total = self.get_object_num("floors_count")
        self.series = self.get_series_type(internal_series)
        self.id = self.create_id()
        self.add_coordinates(self.get_coordinates())
        self.created_at = convert_timestamp_to_utc(
            self.flat["object"]["date_create"])

    def get_object_num(self, key: str) -> int | float:
        object = self.flat["object"]
        if object.get(key) is None:
            raise ValueError(f"{key} is missing")
        return object[key]

    def get_street_name(self) -> str:
        split_street = self.flat["address_name"].split(",")
        if len(split_street) != 3:
            return UNKNOWN
        return f"{split_street[1].strip()} {split_street[2].strip()}"

    def get_series_type(self, internal_series: Dict[str, str]) -> str:
        # check if flat_building_type exists
        object = self.flat["object"]
        if object.get("flat_building_type") is None:
            return UNKNOWN
        series = object["flat_building_type"]
        if series is None:
            return UNKNOWN

        mathed_series = internal_series.get(str(series))
        if mathed_series is None:
            return UNKNOWN
        return mathed_series

    def get_coordinates(self) -> Coordinates:
        latitude = self.flat["latitude"] or 0
        longitude = self.flat["longitude"] or 0
        return Coordinates(latitude, longitude)

    def get_img_url(self) -> str:
        if self.flat["images"] is None or len(self.flat["images"]) <= 0:
            raise ValueError("No images found")
        return self.flat["images"][0]["small"]

    def format_url(self, id: str) -> str:
        return f"https://www.varianti.lv/lv/detail/{id}/"
