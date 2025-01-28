from typing import List
from apscheduler.schedulers.background import BackgroundScheduler


class BaseParser:
    def __init__(self, source: str, scheduler: BackgroundScheduler, deal_type: str):
        self.source = source
        self.scheduler = scheduler
        self.deal_type = deal_type

    def run(self):
        districts = self.get_districts_list()
        self.scrape(districts)
        self.scheduler.add_job(
            self.scrape, "cron", hour="9,12,15,18,21", minute=0, args=[districts])

    def get_districts_list(self) -> List[int | str]:
        raise NotImplementedError

    def scrape(self, districts: List[int]) -> None:
        raise NotImplementedError
