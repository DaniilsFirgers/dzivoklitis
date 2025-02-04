import io
import os
import time
import telebot
from telebot import types
from telebot import types
from scraper.core.postgres import Postgres, Type
from scraper.flat import Flat
from threading import Thread

from scraper.utils.logger import logger


class TelegramBot:
    def __init__(self, postgres: Postgres, sleep: int):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.user_id = os.getenv("TELEGRAM_USER_ID")
        self.bot = telebot.TeleBot(self.token, threaded=True)
        self.postgres = postgres
        self.sleep = sleep

        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            "add_to_favorites:"))(self.handle_add_to_favorites)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            "remove_from_favorites:"))(self.handle_remove_from_favorites)
        self.bot.message_handler(commands=["favorites"])(self.send_favorites)
        self.bot.message_handler(commands=["start"])(self.start)

    def start_polling(self):
        polling_thread = Thread(target=self._start_polling, daemon=True)
        polling_thread.start()

    def start(self):
        self.bot.send_message(
            self.user_id,
            "Hello! I'm a bot that will help you find flats."
            "You can use the following commands:\n"
            "/favorites - to see your favorite flats\n"
        )

    def handle_add_to_favorites(self, call: types.CallbackQuery):
        try:
            id = call.data.split(":")[1]
            if self.postgres.exists_with_id(id, Type.FAVOURITES):
                return self.bot.answer_callback_query(
                    call.id, "Flat already in favorites ❤️"
                )
            self.postgres.add_to_favourites(id)
            logger.info(f"Added a flat with id {id} to favourites.")

            self.bot.answer_callback_query(
                call.id, "Flat added to favorites ❤️"
            )
        except Exception as e:
            logger.error(e)
            self.bot.answer_callback_query(
                call.id, "Error adding a flat to favorites 😢"
            )

    def handle_remove_from_favorites(self, call: types.CallbackQuery):
        try:
            id = call.data.split(":")[1]
            self.postgres.delete(id, Type.FAVOURITES)
            self.bot.answer_callback_query(
                call.id, "Flat removed from favorites 🗑️"
            )
        except Exception as e:
            logger.error(f"Error removing a flat from favorites: {e}")
            self.bot.answer_callback_query(
                call.id, "Error removing a flat from favorites 😢"
            )

    def send_message(self, message: str):
        self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode="Markdown"
        )

    def send_favorites(self, _):
        favorites = self.postgres.get_favourites()
        if not favorites:
            return self.bot.send_message(
                chat_id=self.user_id,
                text="You don't have any favorites yet 😢"
            )
        for counter, favorite in enumerate(favorites, start=1):
            flat = Flat.from_sql_row(*favorite)
            self.send_flat_message(flat, Type.FAVOURITES, counter)

    def send_flat_message(self, flat: Flat, type: Type, counter: str = None):
        msg_txt = self.flat_to_msg(flat, counter)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔍 View URL", url=flat.url),
        )
        if type == Type.FAVOURITES:
            markup.add(
                types.InlineKeyboardButton(
                    "🗑️ Delete", callback_data=f"remove_from_favorites:{flat.id}"),
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "❤️ Add to Favorites", callback_data=f"add_to_favorites:{flat.id}"),
            )

        if flat.image_data is None:
            return self.bot.send_message(
                chat_id=self.user_id,
                text=msg_txt,
                parse_mode="HTML",
                reply_markup=markup
            )

        image_file = io.BytesIO(flat.image_data)
        image_file.name = f"{flat.id}.jpg"
        self.bot.send_photo(
            chat_id=self.user_id,
            photo=image_file,
            caption=msg_txt,
            parse_mode="HTML",
            reply_markup=markup
        )

        time.sleep(self.sleep)

    def flat_to_msg(self, flat: Flat, counter: int = None) -> str:
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

    def _start_polling(self):
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                print(f"Error in bot polling: {e}")
                time.sleep(self.sleep)
                continue
