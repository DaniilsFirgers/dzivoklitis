import os
import toml
import asyncio
import pytz
from pathlib import Path

from scraper.database.postgres import postgres_instance
from scraper.schemas.shared import DealType
from scraper.utils.limiter import RateLimiterQueue
from scraper.parsers.ss import SludinajumuServissParser
from scraper.utils.meta import SingletonMeta
from scraper.utils.logger import logger
from scraper.parsers.city_24 import City24Parser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper.utils.telegram import TelegramBot
from scraper.parsers.pp import PardosanasPortalsParser
from scraper.utils.config import Config, District, ParserConfigs, PpParserConfig, SsParserConfig, City24ParserConfig, TelegramConfig, VariantiParserConfig


class FlatsParser(metaclass=SingletonMeta):
    def __init__(self):
        self.config = self.load_config()
        self.tg_rate_limiter = RateLimiterQueue(rate=30, per=1, buffer=0.2)
        self.telegram_bot = TelegramBot(self.tg_rate_limiter)
        self.scheduler = AsyncIOScheduler()

    def load_config(self):
        config_path = Path("/app/config.toml")
        with open(config_path, "r", encoding="utf-8") as file:
            data = toml.load(file)

        telegram = TelegramConfig(**data["telegram"])

        parsers_data = data["parsers"]
        parsers = ParserConfigs(
            ss=SsParserConfig(**parsers_data["ss"]),
            city24=City24ParserConfig(**parsers_data["city24"]),
            pp=PpParserConfig(**parsers_data["pp"]),
            varianti=VariantiParserConfig(**parsers_data["varianti"])
        )

        districts = [District(**district) for district in data["districts"]]

        return Config(telegram=telegram, parsers=parsers, districts=districts, version=data["version"], name=data["name"])

    async def run(self):
        self.tg_rate_limiter.start()
        asyncio.create_task(self.telegram_bot.start_polling())
        await postgres_instance.init_db()

        self.scheduler.configure(timezone=pytz.timezone("Europe/Riga"))

        admin_tg_id = os.getenv("ADMIN_TELEGRAM_ID")
        if admin_tg_id is not None:
            await self.telegram_bot.send_text_msg_with_limiter(
                f"Bot with version {self.config.version} started", admin_tg_id)

        ss_rent = SludinajumuServissParser(self.telegram_bot, self.config.districts,
                                           self.config.parsers.ss, DealType.RENT)

        ss_sell = SludinajumuServissParser(self.telegram_bot, self.config.districts,
                                           self.config.parsers.ss, DealType.SELL)

        city24_rent = City24Parser(self.telegram_bot, self.config.districts,
                                   self.config.parsers.city24, DealType.RENT)

        city24_sell = City24Parser(self.telegram_bot, self.config.districts,
                                   self.config.parsers.city24, DealType.SELL)

        pp_rent = PardosanasPortalsParser(
            self.telegram_bot, self.config.districts, self.config.parsers.pp, DealType.RENT)

        pp_sell = PardosanasPortalsParser(
            self.telegram_bot, self.config.districts, self.config.parsers.pp, DealType.SELL)

        # NOTE: currently no need tp run all parsers at once
        # await asyncio.gather(ss_sell.run(), city24_sell.run(), pp_sell.run())

        loop = asyncio.get_running_loop()

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            ss_sell.run(), loop), "cron", hour="9,12,15,18,21", minute=0, name="SS_Sell")

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            ss_rent.run(), loop), "cron", hour="9,12,15,18,21", minute=2, name="SS_Rent")

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            city24_sell.run(), loop), "cron", hour="9,12,15,18,21", minute=4, name="City24_Sell")

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            city24_rent.run(), loop), "cron", hour="9,12,15,18,21", minute=6, name="City24_Rent")

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            pp_sell.run(), loop), "cron", hour="9,12,15,18,21", minute=8, name="PP_Sell")

        self.scheduler.add_job(lambda: asyncio.run_coroutine_threadsafe(
            pp_rent.run(), loop), "cron", hour="9,12,15,18,21", minute=10, name="PP_Rent")

        self.scheduler.start()

        for job in self.scheduler.get_jobs():
            logger.info(
                f"Job {job.id} scheduled to run at {job.next_run_time}")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

    async def cleanup(self):
        self.scheduler.shutdown()
        await self.telegram_bot.send_text_msg_with_limiter("Performed cleanup")


if __name__ == "__main__":
    scraper = FlatsParser()
    asyncio.run(scraper.run())
