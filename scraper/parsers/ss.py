import re
from typing import Dict, List
from bs4 import BeautifulSoup, ResultSet, Tag
import requests
from scraper.config import District, SsParserConfig
from scraper.core.postgres import Postgres, Type
from scraper.core.telegram import TelegramBot
from scraper.flat import Coordinates, Flat, SS_Flat
from scraper.parsers.base import BaseParser
from scraper.utils.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from geopy.geocoders import Nominatim


class SSParser(BaseParser):
    def __init__(self, scheduler: BackgroundScheduler, telegram_bot: TelegramBot, postgres: Postgres,
                 districts: List[District], config: SsParserConfig
                 ):

        super().__init__(config.name, scheduler,
                         config.deal_type)
        self.city_name = config.city_name
        self.districts = districts
        self.look_back_arg = config.timeframe
        self.telegram_bot = telegram_bot
        self.postgres = postgres

    def get_districts_list(self) -> List[int]:
        districts_found = []
        url = f"https://www.ss.lv/en/real-estate/flats/{self.city_name.lower()}/"

        try:
            response = requests.get(url, timeout=10)
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
            pages_url = f"https://www.ss.lv/en/real-estate/flats/{self.city_name.lower()}/{district.name}/{self.look_back_arg}/{self.deal_type}/"
            response = requests.get(pages_url)
            bs = BeautifulSoup(response.text, "html.parser")
            all_pages: ResultSet[Tag] = bs.find_all(name="a", class_="navi")

            pages = [1]
            for page_num in all_pages[1:-1]:
                page = int(page_num.get_text())
                pages.append(page)

            for page in pages:
                page_url = f"https://www.ss.lv/real-estate/flats/riga/{district.name}/{self.look_back_arg}/{self.deal_type}/page{page}.html"
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
                    id = description.get("id")

                    chunk: list[Tag] = streets[i:i + 7]
                    raw_info = [street.get_text() for street in chunk]
                    img_url = self.get_image_url(image_urls, i)

                    flat = SS_Flat(url, district, raw_info, img_url)

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
                    if self.postgres.exists_with_id_and_price(flat.id, flat.price_per_m2):
                        continue

                    try:
                        flat.validate()
                    except ValueError:
                        continue

                    coordinates = self.get_coordinates(
                        self.city_name, flat.street)

                    if coordinates is not None:
                        flat.add_coordinates(coordinates)

                    if img_url is not None:
                        flat.load_img()

                    try:
                        self.postgres.add_or_update(flat)
                        logger.info(f"Added flat {flat.id} to the database")
                    except Exception as e:
                        logger.error(e)
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
                counter = f"*{index}/{len(flats)}*"
                self.telegram_bot.send_flat_message(flat, Type.FLATS, counter)

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
