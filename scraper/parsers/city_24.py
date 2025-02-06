
from typing import List

from fake_useragent import UserAgent
import requests
from scraper.config import City24ParserConfig, District, Source
from scraper.core.postgres import Postgres, Type
from scraper.flat import City24_Flat
from scraper.parsers.base import BaseParser
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.core.telegram import TelegramBot
from scraper.schemas.city_24 import City24ResFlatDict
from scraper.utils.logger import logger
from scraper.utils.meta import get_start_of_day


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
        self.user_agent = UserAgent()

    def scrape(self) -> None:
        """Scrape flats from City24.lv
        \n Args:
            districts (Dict[str, str]): A dictionary of districts with their external keys and names.
        """

        for ext_key, district_name in self.districts.items():
            district_info = next(
                (district for district in self.preferred_districts if district.name == district_name), None)
            if district_info is None:
                continue
            # currently we are interested only in a specific deal type (get platform specific deal type by reverse lookup)
            platform_deal_type = next((k for k, v in self.deal_types.items()
                                       if v == self.target_deal_type), None)

            # URL for the API
            url = "https://api.city24.lv/lv_LV/search/realties"

            start_of_day = get_start_of_day()

            # iterate over all the pages
            params = {
                "address[city]": self.city_code,
                "address[district][]": ext_key,
                "tsType":  platform_deal_type,
                "unitType": "Apartment",
                "itemsPerPage": 50,
                "page": 1,
                "datePublished[gte]": start_of_day,
            }

            headers = {
                "User-Agent": self.user_agent.random,
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
                continue

            flats: List[City24ResFlatDict] = response.json()

            for flat in flats:
                new_flat = City24_Flat(
                    district_name, self.target_deal_type, flat)

                try:
                    new_flat.create(self.flat_series)
                except Exception as e:
                    logger.error(f"Error creating flat: {e}")
                    continue
                try:
                    new_flat.validate(district_info)
                except Exception as e:
                    continue

                try:
                    self.postgres.add_or_update(new_flat)
                    logger.info(
                        f"Added {Source.CITY_24.value} flat with id {new_flat.id} in {district_name} to the database")
                except Exception as e:
                    logger.error(e)
                    continue

                self.telegram_bot.send_flat_message(new_flat, Type.FLATS)
