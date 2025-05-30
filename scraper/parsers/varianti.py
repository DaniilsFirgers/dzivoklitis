
import asyncio
from typing import List
import aiohttp
from fake_useragent import UserAgent

from scraper.parsers.flat.varianti import Varianti_Flat
from scraper.schemas.shared import DealType
from scraper.utils.config import VariantiParserConfig, Source
from scraper.database.crud import get_flat, get_matching_filters_tg_user_ids, upsert_flat
from scraper.parsers.base import UNKNOWN, BaseParser
from scraper.utils.telegram import MessageType, TelegramBot
from scraper.schemas.varianti import Flat, VariantiRes
from scraper.utils.logger import logger
from scraper.utils.meta import find_flat_price, get_start_of_day


class VariantiParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot, config: VariantiParserConfig, deal_type: DealType):
        super().__init__(Source.VARIANTI, deal_type)
        self.original_city_code = config.city_code
        self.city_name = self.cities[self.original_city_code]
        self.telegram_bot = telegram_bot
        self.user_agent = UserAgent()
        self.items_per_page = 100
        self.semaphore = asyncio.Semaphore(4)

    async def scrape(self) -> None:
        """Scrape flats from varianti.lv asynchronously"""
        connector = aiohttp.TCPConnector(
            limit_per_host=1, keepalive_timeout=30)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.ensure_future(self.scrape_district(session, platform_district_name, internal_district_name))
                     for platform_district_name, internal_district_name in self.districts.items()]
            await asyncio.gather(*tasks)

    async def scrape_district(self, session: aiohttp.ClientSession, platform_district_name: str, internal_district_name: str):
        """Scrape the entire city asynchronously, handling pagination."""
        async with self.semaphore:
            url = "https://api.varianti.lv/rest/list/ad"

            params = {
                "filters": {
                    "address_country": 1,
                    "deal_type": self.platform_deal_type,
                    "address_district": int(platform_district_name),
                    "is_promoted": False,
                    "features": []
                },
                "page": 0,
                "size": self.items_per_page,
                "order":    {
                    "asc": "false",
                    "field": "DATE"
                },
            }

            headers = {
                "User-Agent": self.user_agent.random,
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
            }

            try:
                async with session.post(url, json=params, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(
                            f"Request failed with status code {response.status} and status text {response}")
                        return

                    varianti_res: VariantiRes = await response.json()

                    if not varianti_res:
                        logger.error(
                            f"No data found for {self.original_city_code}")
                        return

                    if varianti_res["result"]["list"] is None:
                        logger.info(
                            f"No flats found for {self.original_city_code}")
                        return

                    if len(varianti_res["errorDescriptions"]):
                        logger.error(
                            f"Error fetching data for {self.original_city_code} - S {varianti_res['errorDescriptions']}")
                        return

                    await self.process_flats(varianti_res["result"]["list"], session, internal_district_name)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(
                    f"Error fetching data for {self.original_city_code}: {e}")
                return

    async def process_flats(self, flats: List[Flat], session: aiohttp.ClientSession, district_name: str):
        """Process and validate each flat"""
        # As flats are stupidly sorted by created date and not by updated date, we need to filter out old flats
        sorted_flats = self.sort_flats_by_date_update(flats)
        for flat in sorted_flats:
            try:
                need_break = await self.process_flat(flat, session, district_name)
                if need_break:
                    break
            except Exception as e:
                logger.error(f"Error processing flat: {e}")
                continue

    async def process_flat(self, flat_data: Flat, session: aiohttp.ClientSession, district_name: str) -> bool:
        """Process and validate each flat"""
        flat = Varianti_Flat(district_name, self.deal_type,
                             flat_data, self.city_name)

        flat.create(self.flat_series)
        flat.validate()

        if get_start_of_day() > int(flat.created_at.timestamp()):
            logger.info(
                f"Flat update time of {flat.created_at} is older than today's start of day"
            )
            return True

        img_url = flat.get_img_url()
        flat.image_data = await flat.download_img(img_url, session)

        existing_flat = await get_flat(flat.id)

        if existing_flat:
            matched_price = find_flat_price(flat.price, existing_flat.prices)
            if matched_price:
                return False

        flat_orm = flat.to_orm()

        await upsert_flat(flat_orm, flat.price)

        subscribers = await get_matching_filters_tg_user_ids(
            self.city_name, district_name, self.deal_type, rooms=flat.rooms, area=flat.area, price=flat.price, floor=flat.floor)

        for subscriber in subscribers:
            try:
                if existing_flat is None:
                    await self.telegram_bot.send_flat_msg_with_limiter(flat, MessageType.FLATS, tg_user_id=subscriber)
                elif existing_flat is not None and matched_price is None:
                    await self.telegram_bot.send_flat_update_msg_with_limiter(flat, existing_flat.prices, tg_user_id=subscriber)
            except Exception as e:
                logger.error(e)
                continue
        return False

    def sort_flats_by_date_update(self, flats: List[Flat]) -> List[Flat]:
        return sorted(flats, key=lambda x: x["object"].get("date_update", 0), reverse=True)
