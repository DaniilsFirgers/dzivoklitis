import json
from typing import Dict
import asyncio

from scraper.schemas.shared import DealType
from scraper.utils.config import PlatformMapping, Settings, Source
from scraper.utils.logger import logger

UNKNOWN = "Nezināms"


class BaseParser:
    def __init__(self, source: Source, deal_type: DealType):
        self.source = source
        self.deal_type = deal_type
        self.cities, self.districts, self.flat_series, self.platform_deal_type = self.get_settings()
        self.semaphore = asyncio.Semaphore(15)

    async def run(self):
        asyncio.create_task(self.scrape())

    def get_settings(self) -> tuple[Dict[str, str], Dict[str, str], Dict[str, str], str]:
        """Get the settings from the settings.json file.
        \n Returns:
            tuple[Dict[str, str], Dict[str, str], Dict[str, str], str]: A tuple of cities,districts, flat series and platform deal type.
        """
        with open("/app/settings.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        settings = Settings(
            cities=PlatformMapping(**data["cities"]),
            districts=PlatformMapping(**data["districts"]),
            deal_types=PlatformMapping(**data["deal_types"]),
            flat_series=PlatformMapping(**data["flat_series"]))

        districts = self._get_dict(
            self.source, settings.districts, "districts")

        deal_types = self._get_dict(
            self.source, settings.deal_types, "deal_types")
        # match paltform deal type with the one passed in the constructor (one we save to the db)
        platform_deal_type = next(
            (k for k, v in deal_types.items() if v == self.deal_type.value), None)
        if platform_deal_type is None:
            raise ValueError(
                f"Deal type {self.deal_type.value} not found for platform {self.source.value}")

        flat_series = self._get_dict(
            self.source, settings.flat_series, "flat_series")
        cities = self._get_dict(
            self.source, settings.cities, "cities")

        return (cities, districts, flat_series, platform_deal_type)

    def _get_dict(self, source: Source, platform_mapping: PlatformMapping, dict_name: str) -> Dict[str, str]:
        external_map: Dict[str, str] = getattr(platform_mapping, source.value)
        if external_map is None:
            raise ValueError(f"{dict_name} for {source} not found")
        return self._map_dicts(external_map, platform_mapping.reference, dict_name)

    def _map_dicts(self, external_map: Dict[str, str], reference: Dict[str, str], dict_name: str) -> Dict[str, str]:
        """Helper function to map external IDs to internal names."""
        mapped_dict = {}

        for ext_id, internal_id in external_map.items():
            internal_name = reference.get(internal_id)
            if internal_name is None:
                logger.error(
                    f"{dict_name} with external id {ext_id} not found")
                continue
            mapped_dict[ext_id] = internal_name

        return mapped_dict

    async def scrape(self) -> None:
        raise NotImplementedError
