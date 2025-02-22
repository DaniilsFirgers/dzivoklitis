import asyncio
import aiohttp
from typing import List
from bs4 import BeautifulSoup, ResultSet, Tag

from scraper.config import District, Source, SsParserConfig
from scraper.database.crud import flat_exists, get_users, upsert_flat
from scraper.utils.telegram import MessageType, TelegramBot
from scraper.flat import SS_Flat
from scraper.parsers.base import BaseParser
from scraper.utils.logger import logger
from scraper.utils.meta import get_coordinates


class SSParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot, preferred_districts: List[District], config: SsParserConfig):

        super().__init__(Source.SS, config.deal_type)
        self.city_name = config.city_name
        self.preferred_districts = preferred_districts
        self.look_back_arg = config.timeframe
        self.telegram_bot = telegram_bot
        self.semaphore = asyncio.Semaphore(20)

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
        platform_deal_type = next((k for k, v in self.deal_types.items()
                                   if v == self.target_deal_type), None)
        base_url = f"https://www.ss.lv/real-estate/flats/{self.city_name.lower()}/{platform_district_name}/{self.look_back_arg}/{platform_deal_type}/"

        async with self.semaphore:
            first_page_html = await self.fetch_page(session, base_url)

        bs = BeautifulSoup(first_page_html, "lxml")
        all_pages: ResultSet[Tag] = bs.find_all(
            "a", class_="navi")

        pages = [1]
        pages += [int(page_num.get_text()) for page_num in all_pages[1:-1]]

        tasks = [asyncio.create_task(self.scrape_page(session, platform_district_name, internal_district_name, platform_deal_type, page))
                 for page in pages]

        await asyncio.gather(*tasks)

    async def scrape_page(self, session: aiohttp.ClientSession, platform_district_name: str, internal_district_name: str, deal_type: str, page: int):
        """Scrape a single page and extract flat details asynchronously."""
        page_url = f"https://www.ss.lv/real-estate/flats/{self.city_name.lower()}/{platform_district_name}/{self.look_back_arg}/{deal_type}/page{page}.html"

        async with self.semaphore:
            page_html = await self.fetch_page(session, page_url)

        bs = BeautifulSoup(page_html, "lxml")
        descriptions = bs.select("a.am")
        streets = bs.select("td.msga2-o.pp6")
        image_urls = bs.select("img.isfoto.foto_list")

        tasks = []
        for index, (description, streets) in enumerate(zip(descriptions, zip(*[iter(streets)] * 7))):
            img_url = self.get_image_url(image_urls, index)
            tasks.append(asyncio.create_task(
                self.process_flat(description, streets,
                                  img_url, internal_district_name, session)
            ))

        await asyncio.gather(*tasks)

    async def process_flat(self, description: Tag, streets: tuple[Tag], img_url: str, district_name: str, session: aiohttp.ClientSession):
        url = f"https://www.ss.lv/{description.get('href')}"
        raw_info = [street.get_text() for street in streets]

        flat = SS_Flat(url, district_name, raw_info, self.target_deal_type)

        try:
            flat.create(self.flat_series)
        except Exception:
            return

        flat.image_data = await flat.download_img(img_url, session)

        # flat.add_coordinates(await get_coordinates(flat.street, self.city_name))

        try:
            already_in_db = await flat_exists(flat.id, flat.price)
            if already_in_db:
                return
        except Exception as e:
            logger.error(e)
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

        # NOTE: this is a temporary solution to send flats to users whil we are testing the system
        try:
            users = await get_users()
            for user in users:
                await self.telegram_bot.send_flat_msg_with_limiter(flat, MessageType.FLATS, tg_user_id=user.tg_user_id)
        except Exception as e:
            logger.error(e)

    async def scrape(self) -> None:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(
                limit_per_host=10, keepalive_timeout=40)) as session:
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
