from dataclasses import dataclass
from typing import List, Literal


@dataclass(frozen=True)
class GeneralConfig:
    city_name: str
    rooms: int
    deal_type: Literal["buy", "sell", "hand_over"]
    look_back_argument: Literal["today", "today-2", "today-5"]


@dataclass(frozen=True)
class TelegramConfig:
    is_active: bool
    token: str
    chat_id: str


@dataclass(frozen=True)
class GmailConfig:
    is_active: bool
    username: str
    password: str
    to_email: str


@dataclass(frozen=True)
class District:
    name: str
    price_per_m2: int


@dataclass(frozen=True)
class Config:
    general: GeneralConfig
    telegram: TelegramConfig
    gmail: GmailConfig
    districts:    List[District]
