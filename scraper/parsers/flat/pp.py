
from typing import Dict

from scraper.config import Source
from scraper.parsers.base import UNKNOWN
from scraper.schemas.pp import FilterValue, PriceType
from scraper.schemas.shared import Coordinates, DealType
from scraper.parsers.flat.base import Flat
from scraper.schemas.pp import Flat as PpFlat
from scraper.utils.meta import convert_dt_to_utc, try_parse_float, try_parse_int

PP_FILTER_MAP: Dict[str, FilterValue] = {
    "area": {"id": 123, "default": 0},
    "rooms": {"id": 121, "default": 0},
    "floor": {"id": 125, "default": 0},
    "floors_total": {"id": 139, "default": 1},
    "series": {"id": 127, "default": UNKNOWN},
}


class PP_Flat(Flat):
    def __init__(self, district_name: str,  deal_type: DealType, flat: PpFlat, city: str):
        super().__init__(url="", district=district_name,
                         source=Source.PP, deal_type=deal_type)
        self.flat = flat
        self.city = city
        self.price_types = self.get_price_types()

    def create(self, unified_flat_series: Dict[str, str]):
        self.url = self.flat["frontUrl"]
        self.price = self._get_price(self.price_types[0])
        self.price_per_m2 = self._get_price(self.price_types[1])
        self.area = try_parse_float(
            self._get_text_attribute(PP_FILTER_MAP["area"]))
        self.rooms = try_parse_int(
            self._get_text_attribute(PP_FILTER_MAP["rooms"]))
        self.street = self.flat["publicLocation"]["address"] or UNKNOWN
        self.floor = try_parse_int(
            self._get_text_attribute(PP_FILTER_MAP["floor"]))
        self.floors_total = try_parse_int(self._get_text_attribute(
            PP_FILTER_MAP["floors_total"]))
        self.series = self._get_series_type(unified_flat_series)
        self.id = self.create_id()
        self.add_coordinates(self._get_coordinates())
        self.created_at = convert_dt_to_utc(self.flat["publishDate"])

    def _get_price(self, priceType: PriceType) -> int:
        """Get the price of the flat"""
        targetPrice = next(
            (price for price in self.flat["prices"] if price["priceType"]["id"] == priceType.value), None)
        if targetPrice is None:
            return 0
        return try_parse_float(targetPrice["value"])

    def _get_text_attribute(self, filter_value: FilterValue) -> str:
        """Get attributes from the flat filters"""
        attr = next(
            (attr for attr in self.flat["adFilterValues"] if attr["filter"]["id"] == filter_value["id"]), None)
        if attr is None:
            return filter_value["default"]
        return attr["textValue"]

    def _get_series_type(self, unified_flat_series: Dict[str, str]) -> str:
        attr = next(
            (attr for attr in self.flat["adFilterValues"] if attr["filter"]["id"] == PP_FILTER_MAP["series"]["id"]), None)
        if attr is None:
            return PP_FILTER_MAP["series"]["default"]

        if str(attr["value"]["id"]) in unified_flat_series:
            return unified_flat_series[str(attr["value"]["id"])]
        return UNKNOWN

    def get_historic_prices(self) -> list[tuple[str, float]]:
        targetPrice = next(
            (price for price in self.flat["prices"] if price["priceType"]["id"] == self.price_types[0].value), None)
        if targetPrice is None:
            return []
        return [(convert_dt_to_utc(price["timestamp"]), try_parse_float(price["value"])) for price in targetPrice["priceHistory"]]

    def format_img_url(self) -> str:
        extension = self.flat["thumbnail"]["extension"]
        storage_id = self.flat["thumbnail"]["storageId"]
        return f"https://img.pp.lv/storage/{storage_id[0:2]}/{storage_id[2:4]}/{storage_id}/32.{extension}"

    def get_price_types(self) -> tuple[PriceType, PriceType]:
        if self.deal_type == DealType.RENT:
            return PriceType.RENT_FULL, PriceType.RENT_SQUARE
        return PriceType.SELL_FULL, PriceType.SELL_SQUARE

    def _get_coordinates(self) -> Coordinates:
        latitude = self.flat["publicLocation"]["coordinateY"] if self.flat["publicLocation"]["coordinateY"] is not None else 0
        longitude = self.flat["publicLocation"]["coordinateX"] if self.flat["publicLocation"]["coordinateX"] is not None else 0
        return Coordinates(latitude=latitude, longitude=longitude)
