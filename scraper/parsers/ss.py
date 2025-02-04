import re
from typing import Dict, List
from bs4 import BeautifulSoup, ResultSet, Tag
import requests
from scraper.config import District, Source, SsParserConfig
from scraper.core.postgres import Postgres, Type
from scraper.core.telegram import TelegramBot
from scraper.flat import Coordinates,  SS_Flat
from scraper.parsers.base import BaseParser
from scraper.utils.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from geopy.geocoders import Nominatim


class SSParser(BaseParser):
    def __init__(self, scheduler: BackgroundScheduler, telegram_bot: TelegramBot, postgres: Postgres,
                 preferred_districts: List[District], config: SsParserConfig
                 ):

        super().__init__(Source.SS, scheduler,
                         config.deal_type)
        self.city_name = config.city_name
        self.preferred_districts = preferred_districts
        self.look_back_arg = config.timeframe
        self.telegram_bot = telegram_bot
        self.postgres = postgres

    def scrape(self) -> None:
        """Scrape flats from SS.lv
        \n Args:
            districts (Dict[str, str]): A dictionary of districts with their external keys and names.
        """
        # ext_key is centre and district_name is Centrs
        for ext_key, district_name in self.districts.items():
            # currently we will check only districts that are in the preferred_districts list
            district_info = next(
                (district for district in self.preferred_districts if district.name == district_name), None)
            if district_info is None:
                continue

            # currently we are interested only in a specific deal type (get platform specific deal type by reverse lookup)
            platform_deal_type = next((k for k, v in self.deal_types.items()
                                       if v == self.target_deal_type), None)

            pages_url = f"https://www.ss.lv/lv/real-estate/flats/{self.city_name.lower()}/{ext_key}/{self.look_back_arg}/{platform_deal_type}/"
            response = requests.get(pages_url)
            bs = BeautifulSoup(response.text, "html.parser")
            all_pages: ResultSet[Tag] = bs.find_all(name="a", class_="navi")

            pages = [1]
            for page_num in all_pages[1:-1]:
                page = int(page_num.get_text())
                pages.append(page)

            for page in pages:
                page_url = f"https://www.ss.lv/real-estate/flats/{self.city_name.lower()}/{ext_key}/{self.look_back_arg}/{platform_deal_type}/page{page}.html"
                page_res = requests.get(page_url)
                bs = BeautifulSoup(page_res.text, "html.parser")

                descriptions: ResultSet[Tag] = bs.find_all(
                    name="a", class_="am")
                streets: ResultSet[Tag] = bs.find_all(
                    name="td", class_="msga2-o pp6")
                image_urls: ResultSet[Tag] = bs.find_all(
                    name="img", class_="isfoto foto_list")

                # extracting all data about a flat
                for i in range(0, len(streets), 7):
                    # Get a chunk of 7 streets
                    description = descriptions[int(i/7)]
                    info = description.get("href")
                    url = f"https://www.ss.lv/{info}"

                    chunk: list[Tag] = streets[i:i + 7]
                    raw_info = [street.get_text() for street in chunk]
                    img_url = self.get_image_url(image_urls, i)

                    flat = SS_Flat(url, district_name, raw_info,
                                   self.target_deal_type, img_url)

                    # Possible options here:
                    # 1. Flat with this id and price is already in the database -> skip
                    # 2. Flat with this id is already in in the database, but
                    # the price has changed -> update the price and updated_at and
                    # add a new flat_price_update record
                    # 3. Flat with this id is not in the database:
                    #   a. Flat with the same parameters (price, area, rooms, etc.)
                    #   exists in the database and price_per_m2 is the same, but with a different id -> update
                    #   b. Flat with the same parameters (price, area, rooms, etc.) exists in the database,
                    #   but price_per_m2 is different -> update the price and updated_at and add a new flat_price_update record
                    #   c. Flat with the same parameters (price, area, rooms, etc.) does not exist in the database -> add

                    # If flat with the same id and price_per_m2 exists in the database, skip it
                    if self.postgres.exists_with_id_and_price(flat.id, flat.price):
                        continue

                    try:
                        flat.create()
                    except Exception as e:
                        continue

                    try:
                        flat.validate(district_info)
                    except ValueError as e:
                        continue

                    coordinates = self.get_coordinates(
                        self.city_name, flat.street)

                    if coordinates is not None:
                        flat.add_coordinates(coordinates)

                    try:
                        self.postgres.add_or_update(flat)
                        logger.info(
                            f"Added flat {flat.id} - {district_name} to the database")
                    except Exception as e:
                        logger.error(e)
                        continue

                    self.telegram_bot.send_flat_message(flat, Type.FLATS)

    def get_image_url(self, image_urls: ResultSet[Tag], i: int) -> str | None:
        if len(image_urls) == 0:
            return None
        if int(i/7) >= len(image_urls):
            return None
        img_url: str = image_urls[int(i/7)].get("src")
        # Replace thumbnail with full size image
        adjusted_img_url = img_url.replace("th2", "800")
        return adjusted_img_url

    def get_coordinates(self, city: str, street: str) -> Coordinates | None:
        geolocator = Nominatim(user_agent="flats_scraper")
        # Remove sequences of letters followed by a dot (e.g., "J.", "pr.")
        # It helps to get better results
        cleaned_street = re.sub(r'\b[A-Za-z]{1,7}\.\s*', '', street)
        try:
            location = geolocator.geocode({
                "street": cleaned_street,
                "city": city,
                "country": "Latvia"
            })

            if location is None:
                logger.warning(
                    f"Could not find coordinates for {street} in {city}")
                return None

            return Coordinates(location.latitude, location.longitude)
        except Exception as e:
            logger.error(e)
            return None
