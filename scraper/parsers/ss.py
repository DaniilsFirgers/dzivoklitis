import asyncio
import aiohttp
from bs4 import BeautifulSoup, ResultSet, Tag

from scraper.schemas.shared import DealType
from scraper.utils.config import Source, SsParserConfig
from scraper.database.crud import get_matching_filters_tg_user_ids, upsert_flat, get_flat
from scraper.utils.telegram import MessageType, TelegramBot
from scraper.parsers.flat.ss import SS_Flat
from scraper.parsers.base import BaseParser
from scraper.utils.logger import logger
from scraper.utils.meta import find_flat_price, get_coordinates


class SludinajumuServissParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot,  config: SsParserConfig, deal_type: DealType):
        super().__init__(Source.SS, deal_type)
        self.original_city_name = config.city_name
        self.city_name = self.cities[self.original_city_name]
        self.look_back_arg = config.timeframe
        self.telegram_bot = telegram_bot
        self.semaphore = asyncio.Semaphore(4)

    async def fetch_page(self, session: aiohttp.ClientSession, url: str, retries: int = 3, delay: int = 1) -> str:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    return await response.text()
            except aiohttp.ClientError as e:
                logger.info(
                    f"Failed to fetch page {url} - {e}. Retrying {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    return None

    async def scrape_district(self, session: aiohttp.ClientSession, platform_district_name: str, internal_district_name: str):
        """Scrape all pages of a given district asynchronously with request limits."""
        base_url = f"https://www.ss.lv/real-estate/flats/{self.original_city_name}/{platform_district_name}/{self.look_back_arg}/{self.platform_deal_type}/"

        async with self.semaphore:
            first_page_html = await self.fetch_page(session, base_url)

        bs = BeautifulSoup(first_page_html, "lxml")
        all_pages: ResultSet[Tag] = bs.find_all(
            "a", class_="navi")

        pages = [1]
        pages += [int(page_num.get_text()) for page_num in all_pages[1:-1]]

        tasks = [asyncio.create_task(self.scrape_page(session, platform_district_name, internal_district_name, page))
                 for page in pages]

        await asyncio.gather(*tasks)

    async def scrape_page(self, session: aiohttp.ClientSession, platform_district_name: str, internal_district_name: str, page: int):
        """Scrape a single page and extract flat details asynchronously."""
        page_url = f"https://www.ss.lv/real-estate/flats/{self.original_city_name}/{platform_district_name}/{self.look_back_arg}/{self.platform_deal_type}/page{page}.html"

        async with self.semaphore:
            page_html = await self.fetch_page(session, page_url)

        bs = BeautifulSoup(page_html, "lxml")
        descriptions = bs.select("a.am")
        streets = bs.select("td.msga2-o.pp6")
        image_urls = bs.select("img.isfoto.foto_list")

        tasks = []
        for index, (description, streets) in enumerate(zip(descriptions, zip(*[iter(streets)] * 7))):
            img_url = self.get_image_url(image_urls, index)
            try:
                tasks.append(asyncio.create_task(
                    self.process_flat(description, streets,
                                      img_url, internal_district_name, session)
                ))
            except Exception as e:
                logger.error(
                    f"Error processing flat: {e}")
                continue

        await asyncio.gather(*tasks)

    async def process_flat(self, description: Tag, streets: tuple[Tag], img_url: str, district_name: str, session: aiohttp.ClientSession):
        url = f"https://www.ss.lv{description.get('href')}"
        raw_info = [street.get_text() for street in streets]

        flat = SS_Flat(url, district_name, raw_info,
                       self.deal_type, self.city_name)

        try:
            flat.create(self.flat_series)
            flat.validate()
        except Exception as e:
            logger.error(e)
            return

        flat.image_data = await flat.download_img(img_url, session)

        # TODO: move this to a separate task that will limit the amount of requests
        # flat.add_coordinates(await get_coordinates(flat.street, self.city_name))
        try:
            existing_flat = await get_flat(flat.id)
        except Exception as e:
            logger.error(e)
            return
        # Two options here
        # 1. existing_price is none -> flat is new
        # 2. existing_price is not none -> flat is existing, but need to check if price has changed

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

    async def scrape(self) -> None:
        connector = aiohttp.TCPConnector(
            limit_per_host=2, keepalive_timeout=40)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.ensure_future(self.scrape_district(session, platform_district_name, internal_district_name))
                     for platform_district_name, internal_district_name in self.districts.items()]
            await asyncio.gather(*tasks)

    def get_image_url(self, image_urls: ResultSet[Tag], i: int) -> str | None:
        if not image_urls or i >= len(image_urls):
            return None

        img_url: str = image_urls[i].get("src", "")

        if not img_url:
            return None

        return img_url.replace("th2", "800")
