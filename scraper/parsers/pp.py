
import asyncio
from typing import List
import aiohttp
from fake_useragent import UserAgent

from scraper.utils.config import PpParserConfig, Source
from scraper.database.crud import get_flat, get_matching_filters_tg_user_ids, upsert_flat
from scraper.parsers.flat.pp import PP_Flat
from scraper.parsers.base import UNKNOWN, BaseParser
from scraper.schemas.pp import City24ResFlatsDict,  Flat, PriceType
from scraper.schemas.shared import DealType
from scraper.utils.logger import logger
from scraper.utils.meta import find_flat_price, valid_date_published
from scraper.utils.telegram import MessageType, TelegramBot


class PardosanasPortalsParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot, config: PpParserConfig, deal_type: DealType):
        super().__init__(Source.PP, deal_type)
        self.original_city_code = config.city_code
        self.city_name = self.cities[self.original_city_code]
        self.telegram_bot = telegram_bot
        self.user_agent = UserAgent()
        # if there are less than 20, then no need to go to the next page
        self.items_per_page = 20
        self.semaphore = asyncio.Semaphore(5)

    async def scrape(self) -> None:
        """Scrape flats from pp.lv asynchronously."""
        connector = aiohttp.TCPConnector(
            limit_per_host=2, keepalive_timeout=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self.scrape_city(session)

    async def scrape_city(self, session: aiohttp.ClientSession):
        """Scrape the entire city asynchronously, handling pagination."""
        async with self.semaphore:
            url = "https://apipub.pp.lv/lv/api_user/v1/categories/3811/lots"
            price_types = self.get_prices_types()
            page = 1

            while True:
                params = {
                    "region": self.original_city_code,
                    "action": self.get_action(),
                    "orderColumn": "orderDate",
                    "orderDirection": "DESC",
                    "priceTypes[0]": price_types[0].value,
                    "currentPage": page,
                }
                #  include the second price type only if it exists - for selling flats
                if len(price_types) == 2:
                    params["priceTypes[1]"] = price_types[1].value

                headers = {
                    "User-Agent": self.user_agent.random,
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                try:
                    async with session.get(url, headers=headers, params=params, timeout=10) as response:
                        if response.status != 200:
                            logger.error(
                                f"Request failed with status code {response.status} - {response}")
                            page += 1
                            continue
                        data: City24ResFlatsDict = await response.json()

                        if not data or len(data["content"]["data"]) == 0:
                            logger.warning(
                                f"No data found for {self.source} on page {page}, stopping")

                        need_break = await self.process_flats(data, session)

                        if need_break:
                            logger.info(
                                f"Stopping scraping {self.source} for {self.deal_type} on page {page} as the date is too old"
                            )
                            break

                        if len(data["content"]["data"]) < self.items_per_page:
                            logger.warning(
                                f"Less than {self.items_per_page} items found, stopping")
                            break

                except Exception as e:
                    logger.error(
                        f"Request to {self.source} failed with error {e}")
                page += 1

    async def process_flats(self, flats: City24ResFlatsDict, session: aiohttp.ClientSession) -> bool:
        for flat in flats["content"]["data"]:
            if not valid_date_published(flat["publishDate"]):
                return True
            await self._process_flat(flat, session)
        return False

    async def _process_flat(self, flat_data: Flat,  session: aiohttp.ClientSession):
        """Process and validate each flat."""
        district_name = self.get_district_name(flat_data)
        flat = PP_Flat(district_name, self.deal_type,
                       flat_data, self.city_name)

        try:
            flat.create(self.flat_series)
            flat.validate()
        except Exception as e:
            logger.error(f"Error creating flat: {e}")
            return

        img_url = flat.format_img_url()
        flat.image_data = await flat.download_img(img_url, session)

        try:
            existing_flat = await get_flat(flat.id)
        except Exception as e:
            logger.error(e)
            return

        if existing_flat:
            matched_price = find_flat_price(flat.price, existing_flat.prices)
            if matched_price:
                return

        flat_orm = flat.to_orm()
        try:
            await upsert_flat(flat_orm, flat.price)
        except Exception as e:
            logger.error(e)
            return

        try:
            subscribers = await get_matching_filters_tg_user_ids(
                self.city_name, district_name, self.deal_type, rooms=flat.rooms, area=flat.area, price=flat.price, floor=flat.floor)
        except Exception as e:
            logger.error(e)
            return

        for subscriber in subscribers:
            try:
                if existing_flat is None:
                    await self.telegram_bot.send_flat_msg_with_limiter(flat, MessageType.FLATS, tg_user_id=subscriber)
                elif existing_flat is not None and matched_price is None:
                    await self.telegram_bot.send_flat_update_msg_with_limiter(flat, existing_flat.prices, tg_user_id=subscriber)
            except Exception as e:
                logger.error(e)
                continue

    def get_district_name(self, flat: Flat) -> str:
        """ Get district name from district id. """
        if flat["publicLocation"]["region"]["id"] is None:
            return UNKNOWN
        original_district_id = str(
            flat["publicLocation"]["region"]["id"])
        district_name = self.districts.get(original_district_id)
        if district_name is None:
            logger.warning(
                f"Cannot map district with external id {original_district_id}")
            return UNKNOWN
        return district_name

    def get_prices_types(self) -> List[PriceType]:
        """Get the price types for the request."""
        #  We are not interested in daily rent prices
        if self.deal_type == DealType.RENT:
            return [PriceType.RENT_MONTHLY]
        return [PriceType.SELL_FULL, PriceType.SELL_SQUARE]

    def get_action(self) -> int:
        if self.deal_type == DealType.RENT:
            return 5
        return 1
