
import asyncio
from typing import List
import aiohttp
from fake_useragent import UserAgent

from scraper.config import City24ParserConfig, District, Source
from scraper.core.postgres import Postgres, Type
from scraper.flat import City24_Flat
from scraper.parsers.base import BaseParser
from scraper.core.telegram import TelegramBot
from scraper.schemas.city_24 import City24ResFlatDict
from scraper.utils.logger import logger
from scraper.utils.meta import get_start_of_day


class City24Parser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot, postgres: Postgres,
                 preferred_districts: List[District], config: City24ParserConfig
                 ):
        super().__init__(Source.CITY_24, config.deal_type)
        self.city_code = config.city_code
        self.telegram_bot = telegram_bot
        self.postgres = postgres
        self.preferred_districts = preferred_districts
        self.user_agent = UserAgent()
        self.items_per_page = 50

    async def scrape(self) -> None:
        """Scrape flats from City24.lv asynchronously"""
        connector = aiohttp.TCPConnector(
            limit_per_host=5, keepalive_timeout=30)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self.scrape_city(session)

    async def scrape_city(self, session: aiohttp.ClientSession):
        """Scrape the entire city asynchronously, handling pagination."""
        async with self.semaphore:
            platform_deal_type = next(
                (k for k, v in self.deal_types.items() if v == self.target_deal_type), None)
            url = "https://api.city24.lv/lv_LV/search/realties"
            start_of_day = get_start_of_day()
            page = 1

            # 270732 Not found
            while True:
                params = {
                    "address[city]": self.city_code,
                    "tsType": platform_deal_type,
                    "unitType": "Apartment",
                    "itemsPerPage": self.items_per_page,
                    "page": page,
                    "datePublished[gte]": 1738145600,
                }

                headers = {
                    "User-Agent": self.user_agent.random,
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                try:
                    async with session.get(url, params=params, headers=headers, timeout=10) as response:
                        if response.status != 200:
                            logger.error(
                                f"Request failed with status code {response.status}")
                            return
                        print("response", response.url)
                        flats: List[City24ResFlatDict] = await response.json()

                        if not flats:
                            break

                        for flat in flats:
                            await self.process_flat(flat, session)

                        if len(flats) < self.items_per_page:
                            break

                        page += 1

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(
                        f"Error fetching data for {self.city_code} on page {page}: {e}")
                    break  # Stop fetching if an error occurs

    async def process_flat(self, flat_data, session: aiohttp.ClientSession):
        """Process and validate each flat"""

        original_district_id = str(flat_data["address"]["district"]["id"])
        if original_district_id is None:
            logger.warning(
                f"District with external id {original_district_id} not found")
            return

        district = self.districts.get(original_district_id)
        if district is None:
            logger.warning(
                f"Cannot map district with external id {original_district_id}")

        new_flat = City24_Flat(district, self.target_deal_type, flat_data)

        try:
            new_flat.create(self.flat_series)
        except Exception as e:
            logger.error(f"Error creating flat: {e}")
            return
        img_url = new_flat.format_img_url(flat_data["main_image"]["url"])
        new_flat.image_data = await new_flat.download_img(img_url, session)

        print("flat city24", new_flat.id, new_flat.district, new_flat.street)

        # if self.postgres.exists_with_id_and_price(new_flat.id, new_flat.price):
        #     return

        # try:
        #     new_flat.validate(district_info)
        # except Exception:
        #     return

        # try:
        #     self.postgres.add_or_update(new_flat)
        #     logger.info(
        #         f"Added {Source.CITY_24.value} flat with id {new_flat.id} in {district_name} to the database")
        # except Exception as e:
        #     logger.error(e)
        #     return

        await self.telegram_bot.send_flat_message(new_flat, Type.FLATS)
