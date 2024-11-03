from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GeneralConfig:
    city_name: str
    rooms: int


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
