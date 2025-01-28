

from typing import List
from scraper.config import District
from scraper.parsers.base import BaseParser
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.core.telegram import TelegramBot


class City24Parser(BaseParser):
    def __init__(self, scheduler: BackgroundScheduler, telegram_bot: TelegramBot,
                 districts: List[District]
                 ):
        super().__init__(config.name, scheduler,
                         config.deal_type)
