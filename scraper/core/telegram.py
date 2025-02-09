import io
import os
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BufferedInputFile
from scraper.core.postgres import Postgres, Type
from aiogram.filters import Command
from scraper.flat import Flat
from scraper.utils.logger import logger
from scraper.utils.limiter import RateLimiterQueue


class TelegramBot:
    def __init__(self, postgres: Postgres, rate_limiter: RateLimiterQueue):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.user_id = os.getenv("TELEGRAM_USER_ID")
        self.bot = Bot(token=self.token)
        self.dp = Dispatcher()
        self.postgres = postgres
        self.rate_limiter = rate_limiter

        # Register handlers
        self.dp.callback_query.register(
            self.handle_add_to_favorites, F.data.startswith("add_to_favorites:"))
        self.dp.callback_query.register(
            self.handle_remove_from_favorites,  F.data.startswith("remove_from_favorites:"))
        self.dp.message.register(
            self.send_favorites, Command("favorites"))
        self.dp.message.register(self.handle_start, Command("start"))

    async def handle_start(self, message: types.Message):
        """Handles the /start command."""
        await self.bot.send_message(message.chat.id, "Hello! I'm a bot that helps with flats!")

    async def start(self):
        """Starts the bot and sends an initial message."""
        await self.bot.send_message(
            self.user_id,
            "Hello! I'm a bot that will help you find flats.\n"
            "You can use the following commands:\n"
            "/favorites - to see your favorite flats\n"
        )

    async def handle_add_to_favorites(self, call: types.CallbackQuery):
        """Handles adding a flat to favorites."""
        try:
            id = call.data.split(":")[1]
            if self.postgres.exists_with_id(id, Type.FAVOURITES):
                return await self.bot.answer_callback_query(
                    call.id, "Flat already in favorites ❤️"
                )
            self.postgres.add_to_favourites(id)
            logger.info(f"Added a flat with id {id} to favourites.")
            await self.bot.answer_callback_query(call.id, "Flat added to favorites ❤️")
        except Exception as e:
            logger.error(e)
            await self.bot.answer_callback_query(call.id, "Error adding a flat to favorites 😢")

    async def handle_remove_from_favorites(self, call: types.CallbackQuery):
        """Handles removing a flat from favorites."""
        try:
            id = call.data.split(":")[1]
            self.postgres.delete(id, Type.FAVOURITES)
            await self.bot.answer_callback_query(call.id, "Flat removed from favorites 🗑️")
        except Exception as e:
            logger.error(f"Error removing a flat from favorites: {e}")
            await self.bot.answer_callback_query(call.id, "Error removing a flat from favorites 😢")

    async def send_message(self, message: str):
        """Sends a message to the user."""
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode="Markdown"
        )

    async def send_favorites(self, message: types.Message):
        """Sends the list of favorite flats to the user."""
        favorites = self.postgres.get_favourites()
        if not favorites:
            return await self.bot.send_message(
                chat_id=self.user_id,
                text="You don't have any favorites yet 😢"
            )
        await self.send_message("Here are your favorite flats ❤️")
        # for counter, favorite in enumerate(favorites, start=1):
        #     print(favorite)
        #     flat = Flat.from_sql_row(*favorite)
        #     await self.send_flat_message(flat, Type.FAVOURITES, counter)

    async def send_flat_message(self, flat: Flat, type: Type, counter: str = None):
        """Puts a flat message into the rate limiter queue."""
        await self.rate_limiter.add_request(lambda: self._send_flat_message(flat, type, counter))

    async def _send_flat_message(self, flat: Flat, type: Type, counter: str = None):
        """Sends a flat's information message to the user."""
        msg_txt = self.flat_to_msg(flat, counter)

        inline_keyboard = [
            [
                types.InlineKeyboardButton(text="🔍 View URL", url=flat.url)
            ]
        ]

        if type == Type.FAVOURITES:
            inline_keyboard.append(
                [types.InlineKeyboardButton(
                    text="🗑️ Delete", callback_data=f"remove_from_favorites:{flat.id}")]
            )
        else:
            inline_keyboard.append(
                [types.InlineKeyboardButton(
                    text="❤️ Add to Favorites", callback_data=f"add_to_favorites:{flat.id}")]

            )
        markup = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        if flat.image_data is None:
            await self.bot.send_message(
                chat_id=self.user_id,
                text=msg_txt,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )
        else:
            image_file = io.BytesIO(flat.image_data)
            image_file.seek(0)
            photo = BufferedInputFile(
                image_file.read(), filename=f"{flat.id}.jpg")
            await self.bot.send_photo(
                chat_id=self.user_id,
                photo=photo,
                caption=msg_txt,
                parse_mode="HTML",
                reply_markup=markup if markup else None
            )

    def flat_to_msg(self, flat: Flat, counter: int = None) -> str:
        """Generates the message text for a flat."""
        base_msg = (
            f"<b>Source</b>: {flat.source.value}\n"
            f"<b>District</b>: {flat.district}\n"
            f"<b>Street</b>: {flat.street}\n"
            f"<b>Series</b>: {flat.series}\n"
            f"<b>Rooms</b>: {flat.rooms}\n"
            f"<b>M2</b>: {flat.area}\n"
            f"<b>Floor</b>: {flat.floor}/{flat.floors_total}\n"
            f"<b>Price per m2</b>: {flat.price_per_m2}\n"
            f"<b>Full price</b>: {flat.price}\n"
        )

        return f"*Index*: {counter}\n" + base_msg if counter is not None else base_msg

    async def start_polling(self):
        """Start an asyncio task to poll the bot."""
        await self._start_polling()

    async def _start_polling(self):
        """Starts polling the bot asynchronously."""
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error in bot polling: {e}")
            await asyncio.sleep(1)
            await self.start_polling()
