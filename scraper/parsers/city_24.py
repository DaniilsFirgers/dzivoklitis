
import asyncio
from typing import List
import aiohttp
from fake_useragent import UserAgent

from scraper.config import City24ParserConfig, District, Source
from scraper.database.crud import get_flat, get_users, upsert_flat
from scraper.flat import City24_Flat
from scraper.parsers.base import BaseParser
from scraper.utils.telegram import MessageType, TelegramBot
from scraper.schemas.city_24 import City24ResFlatDict
from scraper.utils.logger import logger
from scraper.utils.meta import find_flat_price, get_start_of_day


class City24Parser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot,
                 preferred_districts: List[District], config: City24ParserConfig
                 ):
        super().__init__(Source.CITY_24, config.deal_type)
        self.city_code = config.city_code
        self.telegram_bot = telegram_bot
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
            page = 1

            while True:
                params = {
                    "address[city]": self.city_code,
                    "tsType": platform_deal_type,
                    "unitType": "Apartment",
                    "itemsPerPage": self.items_per_page,
                    "page": page,
                    "datePublished[gte]": get_start_of_day(),
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
        district_name = self.get_district_name(flat_data)
        flat = City24_Flat(district_name, self.target_deal_type, flat_data)

        try:
            flat.create(self.flat_series)
        except Exception as e:
            logger.error(f"Error creating flat: {e}")
            return
        img_url = flat.format_img_url(flat_data["main_image"]["url"])
        flat.image_data = await flat.download_img(img_url, session)

        try:
            existing_flat = await get_flat(flat.id)
        except Exception as e:
            logger.error(e)
            return

        # Two options here
        # 1. existing_price is none -> flat is new
        # 2. existing_price is not none -> flat is existing, but need to check if price has changed
        if existing_flat is not None:
            matched_price = find_flat_price(flat.price, existing_flat.prices)

        # if flat already exists and price is the same, skip
        if existing_flat is not None and matched_price is not None:
            return
        try:
            flat_orm = flat.to_orm()
            await upsert_flat(flat_orm, flat.price)
        except Exception as e:
            logger.error(e)
            return

        try:
            district_info = next(
                (district for district in self.preferred_districts if district.name == district_name), None)
            if district_info is None:
                return
            flat.validate(district_info)
        except ValueError:
            return

        # NOTE: this is a temporary solution to send flats to users while we are testing the system
        try:
            users = await get_users()
            for user in users:
                if existing_flat is None:
                    await self.telegram_bot.send_flat_msg_with_limiter(flat, MessageType.FLATS, tg_user_id=user.tg_user_id)
                elif existing_flat is not None and matched_price is None:
                    await self.telegram_bot.send_flat_update_msg_with_limiter(flat, existing_flat.prices, tg_user_id=user.tg_user_id)
        except Exception as e:
            logger.error(e)

    def get_district_name(self, flat_data) -> str:
        if flat_data["address"]["district"] is None:
            return "Nezināms"
        original = str(flat_data["address"]["district"]["id"])
        district_name = self.districts.get(original)
        if district_name is None:
            logger.warning(
                f"Cannot map district with external id {original}")
            return "Nezināms"
        return district_name
