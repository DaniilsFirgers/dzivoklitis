

from typing import List
from scraper.config import City24ParserConfig, District
from scraper.parsers.base import BaseParser
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.core.telegram import TelegramBot


class City24Parser(BaseParser):
    def __init__(self, scheduler: BackgroundScheduler, telegram_bot: TelegramBot,
                 districts: List[District], config: City24ParserConfig
                 ):
        super().__init__(config.name, scheduler,
                         config.deal_type)
        self.city_code = config.city_code

    def get_districts_list(self):
        pass
