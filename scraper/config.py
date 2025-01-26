from dataclasses import dataclass
from enum import Enum
from typing import List, Literal


class Source(Enum):
    SS = "ss"
    MM = "mm"
    CITY_24 = "city24"


@dataclass(frozen=True)
class SsParserConfig:
    city_name: str
    name: str
    deal_type: Literal["buy", "sell", "hand_over"]
    timeframe: Literal["today", "today-2", "today-5"]


@dataclass
class ParserConfigs:
    ss: SsParserConfig


@dataclass(frozen=True)
class TelegramConfig:
    sleep_time: float


@dataclass(frozen=True)
class District:
    name: str
    max_price_per_m2: int
    min_price_per_m2: int
    rooms: int
    min_m2: int
    min_floor: int
    skip_last_floor: bool


@dataclass(frozen=True)
class Config:
    name: str
    version: str
    parsers: ParserConfigs
    telegram: TelegramConfig
    districts: List[District]
