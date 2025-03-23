
import asyncio
from typing import List
import aiohttp
from fake_useragent import UserAgent

from scraper.schemas.shared import DealType
from scraper.utils.config import City24ParserConfig, District, Source
from scraper.database.crud import get_flat, get_users, upsert_flat
from scraper.parsers.flat.city_24 import City24_Flat
from scraper.parsers.base import UNKNOWN, BaseParser
from scraper.utils.telegram import MessageType, TelegramBot
from scraper.schemas.city_24 import Flat
from scraper.utils.logger import logger
from scraper.utils.meta import find_flat_price, get_start_of_day


class City24Parser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot,
                 preferred_districts: List[District], config: City24ParserConfig, deal_type: DealType
                 ):
        super().__init__(Source.CITY_24, deal_type)
        self.original_city_code = config.city_code
        self.city_name = self.cities[self.original_city_code]
        self.telegram_bot = telegram_bot
        self.preferred_districts = preferred_districts
        self.user_agent = UserAgent()
        # if there are less than 50, then there is no need to go to the next page
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
            url = "https://api.city24.lv/lv_LV/search/realties"
            page = 1

            while True:
                params = {
                    "address[city]": self.original_city_code,
                    "tsType": self.platform_deal_type,
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
                            page += 1
                            continue

                        flats: List[Flat] = await response.json()

                        if not flats:
                            break

                        for flat in flats:
                            try:
                                await self.process_flat(flat, session)
                            except Exception as e:
                                logger.error(
                                    f"Error processing flat: {e}")
                                continue

                        if len(flats) < self.items_per_page:
                            break

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(
                        f"Error fetching data for {self.original_city_code} on page {page}: {e}")
                    break

                page += 1

    async def process_flat(self, flat_data: Flat, session: aiohttp.ClientSession):
        """Process and validate each flat"""
        district_name = self.get_district_name(flat_data)
        flat = City24_Flat(district_name, self.deal_type,
                           flat_data, self.city_name)

        flat.create(self.flat_series)

        img_url = flat.format_img_url()
        flat.image_data = await flat.download_img(img_url, session)

        existing_flat = await get_flat(flat.id)

        if existing_flat:
            matched_price = find_flat_price(flat.price, existing_flat.prices)
            if matched_price:
                return

        flat_orm = flat.to_orm()
        await upsert_flat(flat_orm, flat.price)

        try:
            district_info = next(
                (district for district in self.preferred_districts if district.name == district_name), None)
            if district_info is None:
                return
            flat.validate(district_info)
        except ValueError:
            return

        # NOTE: this is a temporary solution to send flats to users while we are testing the system
        users = await get_users()
        for user in users:
            if existing_flat is None:
                await self.telegram_bot.send_flat_msg_with_limiter(flat, MessageType.FLATS, tg_user_id=user.tg_user_id)
            elif existing_flat is not None and matched_price is None:
                await self.telegram_bot.send_flat_update_msg_with_limiter(flat, existing_flat.prices, tg_user_id=user.tg_user_id)

    def get_district_name(self, flat: Flat) -> str:
        """Get district name from district id"""
        if flat["address"]["district"] is None:
            return UNKNOWN
        original_district_id = str(flat["address"]["district"]["id"])
        district_name = self.districts.get(original_district_id)
        if district_name is None:
            logger.warning(
                f"Cannot map district with external id {original_district_id}")
            return UNKNOWN
        return district_name
