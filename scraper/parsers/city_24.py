

from datetime import datetime, timezone
from typing import List

from fake_useragent import UserAgent
import requests
from scraper.config import City24ParserConfig, District, Source
from scraper.core.postgres import Postgres
from scraper.parsers.base import BaseParser
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.core.telegram import TelegramBot
from scraper.utils.logger import logger


class City24Parser(BaseParser):
    def __init__(self, scheduler: BackgroundScheduler, telegram_bot: TelegramBot, postgres: Postgres,
                 preferred_districts: List[District], config: City24ParserConfig
                 ):
        super().__init__(Source.CITY_24, scheduler,
                         config.deal_type)
        self.city_code = config.city_code
        self.telegram_bot = telegram_bot
        self.postgres = postgres
        self.preferred_districts = preferred_districts

    def scrape(self) -> None:
        """Scrape flats from City24.lv
        \n Args:
            districts (Dict[str, str]): A dictionary of districts with their external keys and names.
        """
        for ext_key, district_name in self.districts.items():
            district_info = next(
                (district for district in self.preferred_districts if district.name == district.name), None)
            if district_info is None:
                continue
            # currently we are interested only in a specific deal type (get platform specific deal type by reverse lookup)
            platform_deal_type = next((k for k, v in self.deal_types.items()
                                       if v == self.target_deal_type), None)

            # URL for the API
            url = "https://api.city24.lv/lv_LV/search/realties"
            ua = UserAgent()

            now = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0)

            # Get the start of the day
            start_of_day = datetime(now.year, now.month, now.day)

            start_of_day_timestamp = int(start_of_day.timestamp())
            # Query parameters
            params = {
                "address[city]": self.city_code,
                "address[district][]": ext_key,
                "tsType":  platform_deal_type,
                "unitType": "Apartment",
                "itemsPerPage": 50,
                "page": 1,
                "datePublished[gte]": start_of_day_timestamp,

            }

            # Headers to mimic a browser request
            headers = {
                "User-Agent": ua.random,
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
            }

            # Make the request
            response = requests.get(
                url, params=params, headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"Request failed with status code {response.status_code}"
                )
                return

            flats = response.json()
            print(flats)
