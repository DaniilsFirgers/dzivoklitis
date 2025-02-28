

from typing import List

import aiohttp
from fake_useragent import UserAgent
from scraper.config import District, PpParserConfig, Source
from scraper.parsers.base import BaseParser
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
        connector = aiohttp.TCPConnector(
            limit_per_host=5, keepalive_timeout=30)
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

            page = 1

            while True:
                url = self.get_url(page, self.target_deal_type)
                headers = {
                    "User-Agent": self.user_agent.random,
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                try:
                    async with session.get(url, headers=headers, timeout=10) as response:
                        data = await response.json()
                except Exception as e:
                    logger.error(
                        f"Request to {self.source} failed with error {e}")
                page += 1

    def get_url(self, page: int, deal_type: str) -> str:
        # 3811 is for apartments
        if deal_type == DealType.RENT:
            return f"https://apipub.pp.lv/lv/api_user/v1/categories/3811/lots?action=5&priceTypes[0]=3&priceTypes[1]=5&region={self.city_code}&orderColumn=orderDate&orderDirection=DESC&currentPage={page}"
        return f"https://apipub.pp.lv/lv/api_user/v1/categories/3811/lots?action=1&priceTypes[0]=1&priceTypes[1]=15&region={self.city_code}&orderColumn=orderDate&orderDirection=DESC&currentPage={page}"
