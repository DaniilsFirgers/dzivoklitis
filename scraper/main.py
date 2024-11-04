import time
from typing import List
from bs4 import BeautifulSoup, ResultSet
import requests
import pandas as pd
import toml
from pathlib import Path
import os
from bs4.element import Tag
from scraper.config import Config, District, GeneralConfig, GmailConfig, TelegramConfig
from scraper.flat import Flat
from scraper.telegram import TelegramBot


class FlatsParser:
    def __init__(self):
        self.config = self.load_config()
        self.telegram_bot = TelegramBot(
            self.config.telegram.token, self.config.telegram.chat_id)

    def load_config(self):

        cwd = os.getcwd()
        config_path = Path(cwd) / "config.toml"
        with open(config_path, "r") as file:
            data = toml.load(file)

        telegram = TelegramConfig(**data["telegram"])
        gmail = GmailConfig(**data["gmail"])
        general = GeneralConfig(**data["general"])
        districts = [District(**district) for district in data["districts"]]

        return Config(telegram=telegram, gmail=gmail, general=general, districts=districts)

    def start(self, districts: List[District]) -> None:
        for district in districts:
            pages_link = f"https://www.ss.lv/en/real-estate/flats/{self.config.general.city_name}/{district.name}/{self.config.general.look_back_argument}/{self.config.general.deal_type}/"
            response = requests.get(pages_link)
            bs = BeautifulSoup(response.text, "html.parser")
            all_pages: ResultSet[Tag] = bs.find_all(name="a", class_="navi")

            pages = [1]
            for page_num in all_pages[1:-1]:
                page = int(page_num.get_text())
                pages.append(page)

            for page in pages:
                page_link = f"https://www.ss.lv/en/real-estate/flats/riga/{district.name}/{self.config.general.look_back_argument}/{self.config.general.deal_type}/page{page}.html"
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

                    chunk = streets[i:i + 7]
                    text = [street.get_text() for street in chunk]

                    flat = Flat(id, link, district.name)
                    flat.add_info(text)
                    self.telegram_bot.send_message(flat)
                    # TODO: Implement a global countrer to limit the number of messages sent
                    # TODO:  hande errors here
                    time.sleep(0.2)

    def get_districts_list(self) -> tuple[List[int], List[str]]:
        districts_found = []
        warnings = []
        link = f"https://www.ss.lv/en/real-estate/flats/{self.config.general.city_name.lower()}/"

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
            for district in self.config.districts:
                try:
                    districts_found.index(district.name)
                    final_districts.append(district)
                except ValueError:
                    warnings.append(f"District {district.name} not found")

            return final_districts, warnings

        except Exception as e:
            raise ValueError(f"Error parsing district data: {e}")


if __name__ == "__main__":
    scraper = FlatsParser()
    try:
        districts, warnings = scraper.get_districts_list()
    except Exception as e:
        # Here we will send intial message to ther messenger if fail the parsing
        print(f"Error: {e}")
    else:
        if warnings:
            # here we will send message to the messenger about warnings
            print("\n".join(warnings))
        scraper.start(districts)
    # main()
