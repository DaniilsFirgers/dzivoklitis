from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Literal

################################# Scraper Config #################################


class Source(Enum):
    SS = "ss"
    MM = "mm"
    CITY_24 = "city24"
    PP = "pp"
    VARIANTI = "varianti"


@dataclass(frozen=True)
class SsParserConfig:
    city_name: str
    name: str
    deal_type: Literal["buy", "sell", "hand_over"]
    timeframe: Literal["today", "today-2", "today-5"]


@dataclass(frozen=True)
class City24ParserConfig:
    name: str
    city_code: str  # Riga = 245396
    deal_type: Literal["sale", "rent"]


@dataclass(frozen=True)
class PpParserConfig:
    name: str
    city_code: str
    deal_type: Literal["1", "5"]


@dataclass(frozen=True)
class VariantiParserConfig:
    name: str
    city_code: str
    deal_type: Literal["sell", "rent"]


@dataclass
class ParserConfigs:
    ss: SsParserConfig
    city24: City24ParserConfig
    pp: PpParserConfig
    varianti: VariantiParserConfig


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


################################ Platform Settings ################################

@dataclass
class PlatformMapping:
    reference: Dict[str, str]  # [id, name]
    ss: Dict[str, str]  # [platform_id, id]
    city24: Dict[str, str]  # [platform_id, id]
    pp: Dict[str, str]  # [platform_id, id]


@dataclass()
class Settings:
    cities: PlatformMapping
    districts: PlatformMapping
    deal_types: PlatformMapping
    flat_series: PlatformMapping
