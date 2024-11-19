import time
from typing import Dict, List
from bs4 import BeautifulSoup, ResultSet
import requests
import toml
from pathlib import Path
from bs4.element import Tag
from scraper.config import Config, District, GeneralConfig, RabbitMq,  TelegramConfig
from scraper.flat import Flat
from scraper.telegram import TelegramBot
from scraper.database import FlatsTinyDb
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from scraper.logger import logger
from scraper.rabbitmq.types import actions
from rabbitmq.client import RabbitMqClient


class FlatsParser:
    def __init__(self):
        self.config = self.load_config()
        self.db = FlatsTinyDb(parsed_db_name=self.config.general.db_name,
                              to_delete_interval=self.config.general.records_delete_interval)
        self.telegram_bot = TelegramBot(
            self.config.telegram.token, self.config.telegram.chat_id, self.db)
        self.rabbitmq_client = RabbitMqClient(
            self.config.rabbitmq, self.db)
        logger.info("FlatsParser initialized", extra={
                    "rabbit": self.rabbitmq_client})

    def load_config(self):
        config_path = Path("/app/config.toml")
        with open(config_path, "r") as file:
            data = toml.load(file)

        telegram = TelegramConfig(**data["telegram"])
        general = GeneralConfig(**data["general"])
        rabbitmq = RabbitMq(**data["rabbitmq"])
        districts = [District(**district) for district in data["districts"]]

        return Config(telegram=telegram, general=general, rabbitmq=rabbitmq, districts=districts)

    def start(self, districts: List[District]) -> None:
        logger.info("Starting the scraper inside 'start' function")
        flats_found: Dict[str, List[Flat]] = {}
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
                    if self.db.exists(id, "parsed"):
                        continue

                    chunk = streets[i:i + 7]
                    text = [street.get_text() for street in chunk]

                    flat = Flat(id, link, district.name)

                    try:
                        flat.add_info(text, district)
                    except ValueError as v:
                        continue

                    self.db.insert(id, flat)
                    if district.name not in flats_found:
                        flats_found[district.name] = [flat]
                    else:
                        flats_found[district.name].append(flat)

        for district, flats in flats_found.items():
            msg = f"Found *{len(flats)}* flats in *{district}*"
            logger.info(msg)
            self.telegram_bot.send_message(msg)
            self.rabbitmq_client.publish(
                action=actions["send_text_message"], message=msg)
            # Iterate over each Student instance in the list of students for that subject
            for index, flat in enumerate(flats, start=1):
                msg = f"*{index}/{len(flats)}*"
                self.telegram_bot.send_flat_message(flat, msg)
                time.sleep(self.config.general.message_sleep)

    def cleanup(self):
        self.db.delete_old_ads()

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
                    warning = f"District {district.name} not found"
                    logger.warning(warning)
                    warnings.append(warning)

            return final_districts, warnings

        except Exception as e:
            raise ValueError(f"Error parsing district data: {e}")


if __name__ == "__main__":
    scraper = FlatsParser()
    try:
        districts, warnings = scraper.get_districts_list()
    except Exception as e:
        scraper.db.close()
        err_msg = f"Error starting scraper: {e}"
        logger.fatal(err_msg)
        scraper.telegram_bot.send_message(err_msg)
    else:
        # some actions in separate threads
        scraper.rabbitmq_client.start_consumers()
        scraper.telegram_bot.start_polling()
        #
        scheduler = BackgroundScheduler()
        scheduler.configure(timezone=pytz.timezone("Europe/Riga"))
        logger.info("Starting the scraper")
        scraper.telegram_bot.send_message("Starting the scraper")
        scraper.start(districts)
        if warnings:
            msg: str = "*Received the following warnings*:\n" + \
                "\n".join(warnings)
            scraper.telegram_bot.send_message(msg)

        scheduler.add_job(scraper.start, "cron",
                          hour="9,12,15,18,21", minute=0, args=[districts])

        scheduler.add_job(scraper.cleanup, "cron", day_of_week="mon",
                          hour=9, minute=0)

        scheduler.start()

        jobs = scheduler.get_jobs()
        for job in jobs:
            logger.info(
                f"Job {job.id} scheduled to run at {job.next_run_time}")

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            scraper.db.close()
            scraper.telegram_bot.send_message("Stopping the scraper")
