

from enum import Enum
from typing import Dict, List

import aiohttp
from fake_useragent import UserAgent
from scraper.config import District, PpParserConfig, Source
from scraper.flat import PP_Flat
from scraper.parsers.base import UNKNOWN_DISTRICT, BaseParser
from scraper.schemas.pp import City24ResFlatsDict,  Flat, PriceType
from scraper.schemas.shared import DealType
from scraper.utils.logger import logger
from scraper.utils.telegram import TelegramBot


class PardosanasPortalsParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot,
                 preferred_districts: List[District], config: PpParserConfig
                 ):
        super().__init__(Source.PP, config.deal_type)
        self.city_code = config.city_code
        self.telegram_bot = telegram_bot
        self.preferred_districts = preferred_districts
        self.user_agent = UserAgent()
        # if there are less than 20, then no need to go to the next page
        self.items_per_page = 20

    async def scrape(self) -> None:
        """Scrape flats from pp.lv asynchronously"""
        logger.warning(f"Scraping {self.source} for {self.target_deal_type}")
        connector = aiohttp.TCPConnector(
            limit_per_host=5, keepalive_timeout=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self.scrape_city(session)

    async def scrape_city(self, session: aiohttp.ClientSession):
        """Scrape the entire city asynchronously, handling pagination."""
        async with self.semaphore:
            platform_deal_type = next(
                (k for k, v in self.deal_types.items() if v == self.target_deal_type), None)
            if platform_deal_type is None:
                logger.error(
                    f"Deal type {self.target_deal_type} not found in {self.source}")
                return

            url = "https://apipub.pp.lv/lv/api_user/v1/categories/3811/lots"
            price_types = self.get_prices_types(self.target_deal_type)
            page = 1

            logger.warning(
                f"Scraping {self.source} for {self.target_deal_type} in {self.city_code}")

            while True:
                params = {
                    "region": self.city_code,
                    "action": self.get_action(self.target_deal_type),
                    "orderColumn": "orderDate",
                    "orderDirection": "DESC",
                    "priceTypes[0]": price_types[0],
                    "priceTypes[1]": price_types[1],
                    "currentPage": page,
                }

                logger.warning(
                    f"Requesting {self.source} with params {params} on page {page}")

                headers = {
                    "User-Agent": self.user_agent.random,
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                try:
                    async with session.get(url, headers=headers, params=params, timeout=10) as response:
                        logger.warning(
                            f"Requesting {self.source} with params {params} on page {page}")
                        if response.status != 200:
                            logger.error(
                                f"Request failed with status code {response.status} - {response}")
                            page += 1
                            continue

                        data: City24ResFlatsDict = await response.json()

                        if not data or len(data["content"]["data"]) == 0:
                            logger.warning(
                                f"No data found for {self.source} on page {page}, stopping")

                        await self.process_flats(data, session)

                        if len(data["content"]["data"]) < self.items_per_page:
                            logger.warning(
                                f"Less than {self.items_per_page} items found, stopping")
                            break

                except Exception as e:
                    logger.error(
                        f"Request to {self.source} failed with error {e}")
                page += 1

    async def process_flats(self, flats: City24ResFlatsDict, session: aiohttp.ClientSession):
        for flat in flats["content"]["data"]:
            await self._process_flat(flat, session)

    async def _process_flat(self, flat_data: Flat,  session: aiohttp.ClientSession):
        """Process and validate each flat"""
        district_name = self.get_district_name(flat_data)
        flat = PP_Flat(district_name, self.target_deal_type, flat_data)
        try:
            flat.create(self.flat_series)
            logger.info(f"Processing flat {flat.id}")
        except Exception as e:
            logger.error(f"Error creating flat: {e}")
            return

    def get_district_name(self, flat: Flat) -> str:
        """Get district name from district id"""
        if flat["publicLocation"]["region"]["id"] is None:
            return UNKNOWN_DISTRICT
        original_district_id = str(flat["publicLocation"]["region"]["id"])
        district_name = self.districts.get(original_district_id)
        if district_name is None:
            logger.warning(
                f"Cannot map district with external id {original_district_id}")
            return UNKNOWN_DISTRICT
        return district_name

    def get_prices_types(self, deal_type: str) -> List[int]:
        if deal_type == DealType.RENT:
            return [PriceType.RENT_FULL.value, PriceType.RENT_SQUARE.value]
        return [PriceType.SELL_FULL.value, PriceType.SELL_SQUARE.value]

    def get_action(self, deal_type: str) -> int:
        if deal_type == DealType.RENT:
            return 5
        return 1
