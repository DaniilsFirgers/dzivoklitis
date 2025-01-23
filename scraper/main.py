import time
import toml
from pathlib import Path
from scraper.config import Config, District, ParserConfigs, SsParserConfig, TelegramConfig, PostgresConfig
from scraper.core.telegram import TelegramBot
from scraper.core.postgres import Postgres
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from scraper.utils.logger import logger
from scraper.utils.meta import SingletonMeta
from scraper.parsers.ss import SSParser


class FlatsParser(metaclass=SingletonMeta):
    def __init__(self):
        self.config = self.load_config()
        self.postgres = Postgres(
            self.config.postgres.host, self.config.postgres.port, self.config.postgres.user, self.config.postgres.password, self.config.postgres.database)
        self.telegram_bot = TelegramBot(
            self.config.telegram.token, self.config.telegram.chat_id, self.postgres)
        self.scheduler = BackgroundScheduler()

    def load_config(self):
        config_path = Path("/app/config.toml")
        with open(config_path, "r") as file:
            data = toml.load(file)

        telegram = TelegramConfig(**data["telegram"])

        parsers_data = data["parsers"]
        parsers = ParserConfigs(
            ss=SsParserConfig(**parsers_data["ss"])
        )
        postgres = PostgresConfig(**data["postgres"])
        districts = [District(**district) for district in data["districts"]]

        return Config(telegram=telegram, parsers=parsers, districts=districts, postgres=postgres)

    def run(self):
        self.telegram_bot.start_polling()
        self.scheduler.configure(timezone=pytz.timezone("Europe/Riga"))
        self.postgres.connect()

        self.telegram_bot.send_message("Bot started")

        ss = SSParser(self.scheduler, self.telegram_bot, self.postgres,
                      self.config.districts, self.config.parsers.ss, self.config.telegram.sleep_time)
        ss.run()

        self.scheduler.start()
        for job in self.scheduler.get_jobs():
            logger.info(
                f"Job {job.id} scheduled to run at {job.next_run_time}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        self.postgres.close()
        self.scheduler.shutdown()
        self.telegram_bot.send_message("Performed cleanup")


if __name__ == "__main__":
    scraper = FlatsParser()
    scraper.run()
