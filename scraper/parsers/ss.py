import time
from typing import Dict, List
from bs4 import BeautifulSoup, ResultSet, Tag
import requests
from scraper.config import District, GeneralConfig
from scraper.core.postgres import Postgres, Table
from scraper.core.telegram import TelegramBot
from scraper.flat import Flat
from scraper.parsers.base import BaseParser
from scraper.utils.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler


class SSParser(BaseParser):
    def __init__(self, source: str, scheduler: BackgroundScheduler, telegram_bot: TelegramBot, postgres: Postgres,
                 districts: List[District], general_config: GeneralConfig
                 ):
        super().__init__(source, scheduler,
                         general_config.deal_type, general_config.message_sleep)
        self.city_name = general_config.city_name
        self.districts = districts
        self.look_back_arg = general_config.look_back_argument
        self.telegram_bot = telegram_bot
        self.postgres = postgres

    def get_districts_list(self) -> List[int]:
        districts_found = []
        link = f"https://www.ss.lv/en/real-estate/flats/{self.city_name.lower()}/"

        try:
            response = requests.get(link, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:

            raise ValueError(f"Error accessing the website: {e}")

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            district_elements = soup.find_all(name="h4", class_="category")

            if not district_elements:
                raise ValueError("No district elements found on page")

            for index, district in enumerate(district_elements):
                area: str = district.getText().strip().lower().replace(" ", "-")
                districts_found.append(area)

                if index == 38:  # Optional limit on number of districts
                    break

            final_districts = []
            for district in self.districts:
                try:
                    districts_found.index(district.name)
                    final_districts.append(district)
                except ValueError:
                    warning = f"District {district.name} not found"
                    logger.warning(warning)

            return final_districts

        except Exception as e:
            raise ValueError(f"Error parsing district data: {e}")

    def scrape(self, districts: List[District]) -> None:
        flats_found: Dict[str, List[Flat]] = {}
        for district in districts:
            pages_link = f"https://www.ss.lv/en/real-estate/flats/{self.city_name.lower()}/{district.name}/{self.look_back_arg}/{self.deal_type}/"
            response = requests.get(pages_link)
            bs = BeautifulSoup(response.text, "html.parser")
            all_pages: ResultSet[Tag] = bs.find_all(name="a", class_="navi")

            pages = [1]
            for page_num in all_pages[1:-1]:
                page = int(page_num.get_text())
                pages.append(page)

            for page in pages:
                page_link = f"https://www.ss.lv/en/real-estate/flats/riga/{district.name}/{self.look_back_arg}/{self.deal_type}/page{page}.html"
                page_res = requests.get(page_link)
                bs = BeautifulSoup(page_res.text, "html.parser")

                descriptions: ResultSet[Tag] = bs.find_all(
                    name="a", class_="am")
                streets: ResultSet[Tag] = bs.find_all(
                    name="td", class_="msga2-o pp6")

                # extracting all data about a flat
                for i in range(0, len(streets), 7):
                    # Get a chunk of 7 streets
                    description = descriptions[int(i/7)]
                    info = description.get("href")
                    link = f"https://www.ss.lv/{info}"
                    id = description.get("id")

                    if self.postgres.check_if_exists(id, Table.FLATS):
                        continue
                    chunk: list[Tag] = streets[i:i + 7]
                    text = [street.get_text() for street in chunk]
                    flat = Flat(id, link, district.name, self.source)

                    try:
                        flat.add_info(text, district)
                    except ValueError:
                        continue

                    try:
                        self.postgres.add(flat)
                        logger.info(f"Added flat {flat.id} to the database")
                    except Exception as e:
                        logger.error(
                            f"Error adding a flat to the database: {e}")
                        continue

                    if district.name not in flats_found:
                        flats_found[district.name] = [flat]
                    else:
                        flats_found[district.name].append(flat)

        for district, flats in flats_found.items():
            msg = f"Found *{len(flats)}* flats in *{district}*"
            logger.info(msg)
            self.telegram_bot.send_message(msg)

            for index, flat in enumerate(flats, start=1):
                msg = f"*{index}/{len(flats)}*"
                self.telegram_bot.send_flat_message(flat, msg)
                time.sleep(self.sleep_time)
