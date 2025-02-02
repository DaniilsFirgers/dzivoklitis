import json
from typing import Dict
from apscheduler.schedulers.background import BackgroundScheduler

from scraper.config import DealTypes, Districts, Settings, Source
from scraper.utils.logger import logger


class BaseParser:
    def __init__(self, source: Source, scheduler: BackgroundScheduler, target_deal_type: str):
        self.source = source
        self.scheduler = scheduler
        self.target_deal_type = target_deal_type
        self.districts = {}
        self.deal_types = {}

    def run(self):
        self.districts, self.deal_types = self.get_settings()
        self.scrape()
        self.scheduler.add_job(
            self.scrape, "cron", hour="9,12,15,18,21", minute=0)

    def get_settings(self) -> tuple[Dict[str, str], Dict[str, str]]:
        """Get the settings from the settings.json file.
        \n Returns:
            tuple[Dict[str, str], Dict[str, str]]: A tuple of districts and deal types.
        """
        with open("/app/settings.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        settings = Settings(districts=Districts(
            **data["districts"]), deal_types=DealTypes(**data["deal_types"]))

        districts_source_map = {
            Source.SS: settings.districts.ss,
            Source.CITY_24: settings.districts.city24
        }

        deal_types_source_map = {
            Source.SS: settings.deal_types.ss,
            Source.CITY_24: settings.deal_types.city24
        }

        if self.source not in districts_source_map:
            raise NotImplementedError(f"Source {self.source} not supported")

        districts = self._map_districts(
            districts_source_map[self.source], settings.districts.reference)
        deal_types = self._map_deal_types(
            deal_types_source_map[self.source], settings.deal_types.reference)
        return (districts, deal_types)

    def _map_districts(self, external_map: Dict[str, str], reference: Dict[str, str]) -> Dict[str, str]:
        """Helper function to map external IDs to district names."""
        mapped_districts = {}

        for ext_id, internal_id in external_map.items():
            district_name = reference.get(internal_id)
            if district_name is None:
                logger.error(f"District with external id {ext_id} not found")
                continue
            mapped_districts[ext_id] = district_name

        return mapped_districts

    def _map_deal_types(self, deal_types: Dict[str, str], reference: Dict[str, str]) -> Dict[str, str]:
        """Helper function to map external IDs to deal type names."""
        mapped_deal_types = {}

        for ext_id, internal_id in deal_types.items():
            deal_type_name = reference.get(internal_id)
            if deal_type_name is None:
                logger.error(f"Deal type with external id {ext_id} not found")
                continue
            mapped_deal_types[ext_id] = deal_type_name

        return mapped_deal_types

    def scrape(self) -> None:
        raise NotImplementedError
