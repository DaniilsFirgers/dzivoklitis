from typing import List
from bs4 import BeautifulSoup, ResultSet
import requests
import pandas as pd
import toml
from pathlib import Path
import os
from bs4.element import Tag
import re

from scraper.config import Config, District, GeneralConfig, GmailConfig, TelegramConfig


class Flat:
    def __init__(self, id: str, link: str):
        self.id = id
        self.link = link

    def add_info(self, raw_info: list[str]):
        if len(raw_info) != 7:
            raise ValueError("Incorrect number of elements in raw_info")
        self.street = raw_info[0]
        self.rooms = int(raw_info[1])
        self.m2 = float(raw_info[2])
        self.floor = raw_info[3]
        self.series = raw_info[4]
        self.price_per_m2 = int(re.sub(r"[^\d]", "", raw_info[5]))
        self.full_price = int(re.sub(r"[^\d]", "", raw_info[6]))


class FlatsParser:
    def __init__(self):
        self.config = self.load_config()

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

            flats = []

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

                    flat = Flat(id, link)
                    flat.add_info(text)
                    flats.append(flat)

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
