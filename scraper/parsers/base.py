from typing import List
from apscheduler.schedulers.background import BackgroundScheduler


class BaseParser:
    def __init__(self, source: str, scheduler: BackgroundScheduler, deal_type: str, sleep_time: int = 3):
        self.source = source
        self.scheduler = scheduler
        self.deal_type = deal_type
        self.sleep_time = sleep_time

    def run(self):
        districts = self.get_districts_list()
        self.scrape(districts)
        self.scheduler.add_job(
            self.scrape, "cron", hour="9,12,15,18,21", minute=0, args=[districts])

    def get_districts_list(self) -> List[int]:
        raise NotImplementedError

    def scrape(self, districts: List[int]) -> None:
        raise NotImplementedError
