

from typing import List

import aiohttp
from fake_useragent import UserAgent
from scraper.config import District, PpParserConfig, Source
from scraper.parsers.base import BaseParser
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
