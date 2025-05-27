from enum import Enum
import os
import asyncio
from datetime import datetime
from typing import List

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BufferedInputFile
from aiogram.filters import Command
from aiogram.types import BotCommand
from scraper.database.crud import add_favorite, remove_favorite, get_favourites
from scraper.database.models.price import Price
from scraper.parsers.flat.base import Flat
from scraper.utils.logger import logger
from scraper.utils.limiter import RateLimiterQueue


class MessageType(Enum):
    FLATS = "flats"
    FAVOURITES = "favourites"


class TelegramBot:
    def __init__(self, rate_limiter: RateLimiterQueue):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.bot = Bot(token=self.token)
        self.dp = Dispatcher()
        self.rate_limiter = rate_limiter

        # Register handlers
        self.dp.callback_query.register(
            self.handle_add_to_favorites, F.data.startswith("add_to_favorites:"))
        self.dp.callback_query.register(
            self.handle_remove_from_favorites,  F.data.startswith("remove_from_favorites:"))
        self.dp.message.register(
            self.send_favorites, Command("favorites"))
        self.dp.message.register(self.handle_start, Command("start"))

    async def set_bot_commands(self):
        commands = [
            BotCommand(command="start", description="Uzsākt botu"),
            BotCommand(command="favorites",
                       description="Apskatīt favorītu dzīvokļu sludinājumus"),
            BotCommand(command="settings",
                       description="Pielāgojiet filtra iestatījumus"),
        ]
        await self.bot.set_my_commands(commands)

    async def handle_start(self, message: types.Message):
        """Handles the /start command."""
        text = "Sveiki! Esmu bots, kas jums palīdzēs saņemt nekustamā īpašuma sludinājumu paziņojumus un sekot līdzi cenu izmaiņām!"
        await self.send_text_msg_with_limiter(text, message.from_user.id)

    async def handle_add_to_favorites(self, call: types.CallbackQuery):
        """Handles adding a flat to favorites."""
        try:
            id = call.data.split(":")[1]
            if await add_favorite(id, call.from_user.id):
                logger.info(f"Added a flat with id {id} to favorites.")
                await self.bot.answer_callback_query(call.id, "Dzīvoklis tika pievienots favorītiem ❤️")
            else:
                await self.bot.answer_callback_query(call.id, "Dzīvoklis jau ir starp favorītiem ❤️")
        except Exception as e:
            logger.error(e)
            await self.bot.answer_callback_query(call.id, "Error adding a flat to favorites 😢")

    async def handle_remove_from_favorites(self, call: types.CallbackQuery):
        """Handles removing a flat from favorites."""
        try:
            id = call.data.split(":")[1]
            await remove_favorite(id, call.from_user.id)
            await self.bot.answer_callback_query(call.id, "Dzīvokļa sludinājums izdzēsts no favorītiem 🗑️")
        except Exception as e:
            logger.error(f"Error removing a flat from favorites: {e}")
            await self.bot.answer_callback_query(call.id, "Kļūda, dzēšot dzīvokļa sludinājumu no favorītiem 😢")

    async def send_text_msg_with_limiter(self, message: str, tg_user_id: int):
        """Sends a message to the user."""
        await self.rate_limiter.add_request(lambda: self._send_text_message(message, tg_user_id))

    async def _send_text_message(self, message: str, tg_user_id: int):
        """Sends a message to the user."""
        await self.bot.send_message(
            chat_id=tg_user_id,
            text=message,
            parse_mode="Markdown"
        )

    async def send_favorites(self, message: types.Message):
        """Sends the list of favorite flats to the user."""
        favorites = await get_favourites(message.from_user.id)
        if not favorites:
            text = "Jūs vēl neesat pievienojis nevienu iecienītāko dzīvokli 😢"
            return await self.send_text_msg_with_limiter(text, message.from_user.id)
        text = "Šeit ir jūsu iecienītākie dzīvokļi ❤️"
        await self.send_text_msg_with_limiter(text, message.from_user.id)
        for counter, favorite in enumerate(favorites, start=1):
            flat = Flat.from_orm(favorite)
            await self.send_flat_msg_with_limiter(flat, MessageType.FAVOURITES, message.from_user.id, counter)

    async def send_flat_msg_with_limiter(self, flat: Flat, type: MessageType, tg_user_id: int, counter: str = None):
        """Puts a flat message into the rate limiter queue."""
        await self.rate_limiter.add_request(lambda: self._send_flat_message(flat, type, tg_user_id, counter))

    async def send_flat_update_msg_with_limiter(self, flat: Flat, prev_prices: List[Price], tg_user_id: int):
        """Puts a flat update message into the rate limiter queue."""
        await self.rate_limiter.add_request(lambda: self._send_flat_update_message(flat, prev_prices, tg_user_id))

    async def _send_flat_message(self, flat: Flat, type: MessageType, tg_user_id: int, counter: str = None):
        """Sends a flat's information message to the user."""
        text = self.flat_to_msg(flat, counter)

        inline_keyboard = [
            [
                types.InlineKeyboardButton(text="🔍Aplūkot URL", url=flat.url)
            ]
        ]

        if type == MessageType.FAVOURITES:
            inline_keyboard.append(
                [types.InlineKeyboardButton(
                    text="🗑️ Izdzēst", callback_data=f"remove_from_favorites:{flat.id}")]
            )
        else:
            inline_keyboard.append(
                [types.InlineKeyboardButton(
                    text="❤️ Pievienot favorītiem", callback_data=f"add_to_favorites:{flat.id}")]

            )
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        if flat.image_data is None:
            await self.bot.send_message(
                chat_id=tg_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )
        else:
            photo = BufferedInputFile(
                flat.image_data, filename=f"{flat.id}.jpg")
            await self.bot.send_photo(
                chat_id=tg_user_id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )

    async def _send_flat_update_message(self, flat: Flat, prev_prices: List[Price], tg_user_id: int):
        """Sends a flat's update message to the user."""

        text = self.flat_update_to_msg(flat, prev_prices)

        inline_keyboard = [
            [
                types.InlineKeyboardButton(text="🔍Aplūkot URL", url=flat.url)
            ],
            [types.InlineKeyboardButton(
                text="❤️ Pievienot favorītiem", callback_data=f"add_to_favorites:{flat.id}")
             ]
        ]

        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        if flat.image_data is None:
            await self.bot.send_message(
                chat_id=tg_user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )
        else:
            photo = BufferedInputFile(
                flat.image_data, filename=f"{flat.id}.jpg")
            await self.bot.send_photo(
                chat_id=tg_user_id,
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )

    def flat_update_to_msg(self, flat: Flat, prices_info: List[Price]) -> str:
        prices_info = sorted(
            prices_info, key=lambda x: x.updated_at, reverse=False)
        last_price = prices_info[len(
            prices_info) - 1].price if prices_info else flat.price

        msg_title = "🎉 Cenas kritums!" if last_price > flat.price else "😢 Cenas pieaugums!"

        price_history_text = "<b>Cenu vēsture: </b>\n"

        prev_price = None
        for price_info in prices_info:
            date = price_info.updated_at.strftime("%d.%m.%Y")

            if prev_price is None:
                line = f"    <i>{date}</i>: {price_info.price}€\n"
            else:
                price_change = (
                    (price_info.price - prev_price) / prev_price) * 100
                arrow = "🔽" if price_change < 0 else "🔼"
                line = f"    <i>{date}</i>: {price_info.price}€ ({arrow} {abs(price_change):.2f}%)\n"

            price_history_text = line + price_history_text
            prev_price = price_info.price

        if prev_price:
            date = flat.created_at.strftime("%d.%m.%Y")
            price_change = ((flat.price - prev_price) / prev_price) * 100
            arrow = "🔽" if price_change < 0 else "🔼"
            current_price_line = f"    <i>{date}</i>: {flat.price}€ ({arrow} {abs(price_change):.2f}%)\n"
            price_history_text = current_price_line + price_history_text

        else:
            date = flat.created_at.strftime("%d.%m.%Y")
            current_price_line = f"    <i>{date}</i>: {flat.price}€\n"
            price_history_text = current_price_line + price_history_text

        text = (
            f"<b>{msg_title}</b>\n"
            f"<b>Avots</b>: {flat.source.value}\n"
            f"<b>Darījums</b>: {flat.deal_type}\n"
            f"<b>Pilsēta</b>: {flat.city}\n"
            f"<b>Apkaime</b>: {flat.district}\n"
            f"<b>Iela</b>: {flat.street}\n"
            f"<b>Sērija</b>: {flat.series}\n"
            f"<b>Istabas</b>: {flat.rooms}\n"
            f"<b>Platība</b>: {flat.area}\n"
            f"<b>Stāvs</b>: {flat.floor}/{flat.floors_total}\n"
            f"<b>Cena €/m²</b>: {flat.price_per_m2}\n"
            f"<b>Cena €</b>: {flat.price}\n"
            f"{price_history_text}"
        )
        return text

    def flat_to_msg(self, flat: Flat, counter: int = None) -> str:
        """Generates the message text for a flat."""
        text = (
            f"<b>Avots</b>: {flat.source.value}\n"
            f"<b>Darījums</b>: {flat.deal_type}\n"
            f"<b>Pilsēta</b>: {flat.city}\n"
            f"<b>Apkaime</b>: {flat.district}\n"
            f"<b>Iela</b>: {flat.street}\n"
            f"<b>Sērija</b>: {flat.series}\n"
            f"<b>Istabas</b>: {flat.rooms}\n"
            f"<b>Platība</b>: {flat.area}\n"
            f"<b>Stāvs</b>: {flat.floor}/{flat.floors_total}\n"
            f"<b>Cena €/m²</b>: {flat.price_per_m2}\n"
            f"<b>Cena €</b>: {flat.price}\n"
        )

        return f"<b>Numurs</b>: {counter}\n" + text if counter is not None else text

    async def start_polling(self):
        """Start an asyncio task to poll the bot."""
        await self.set_bot_commands()
        await self._start_polling()

    async def _start_polling(self):
        """Starts polling the bot asynchronously."""
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error in bot polling: {e}")
            await asyncio.sleep(1)
            await self.start_polling()
