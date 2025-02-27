

from typing import List

from fake_useragent import UserAgent
from scraper.config import District, PpParserConfig, Source
from scraper.parsers.base import BaseParser
from scraper.utils.telegram import TelegramBot


class PpParser(BaseParser):
    def __init__(self, telegram_bot: TelegramBot,
                 preferred_districts: List[District], config: PpParserConfig
                 ):
        super().__init__(Source.PP, config.deal_type)
        self.city_code = config.city_code
        self.telegram_bot = telegram_bot
        self.preferred_districts = preferred_districts
        self.user_agent = UserAgent()
        # if there are less than 20, then no need to go to the next page
        self.items_per_page = 20
