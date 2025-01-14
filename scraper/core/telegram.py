import time
import telebot
from telebot import types
from telebot import types
from scraper.core.postgres import Postgres, Table
from scraper.flat import Flat
from threading import Thread

from scraper.utils.logger import logger


class TelegramBot:
    def __init__(self, token: str, chat_id: str, postgres: Postgres):
        self.bot = telebot.TeleBot(token, threaded=True)
        self.chat_id = chat_id
        self.postgres = postgres

        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            "add_to_favorites:"))(self.handle_add_to_favorites)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            "remove_from_favorites:"))(self.handle_remove_from_favorites)
        self.bot.message_handler(commands=["favorites"])(self.send_favorites)

    def start_polling(self):
        polling_thread = Thread(target=self._start_polling, daemon=True)
        polling_thread.start()

    def handle_add_to_favorites(self, call: types.CallbackQuery):
        try:
            id = call.data.split(":")[1]
            if self.postgres.check_if_exists(id, Table.FAVOURITE_FLATS):
                return self.bot.answer_callback_query(
                    call.id, "Flat already in favorites ❤️"
                )
            self.postgres.add_to_favourites(id)
            logger.info(f"Added a flat with id {id} to favourites.")

            self.bot.answer_callback_query(
                call.id, "Flat added to favorites ❤️"
            )
        except Exception as e:
            logger.error(f"Error adding a flat to favorites: {e}")
            self.bot.answer_callback_query(
                call.id, "Error adding a flat to favorites 😢"
            )

    def handle_remove_from_favorites(self, call: types.CallbackQuery):
        try:
            id = call.data.split(":")[1]
            self.postgres.delete(id, Table.FAVOURITE_FLATS)
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
            chat_id=self.chat_id,
            text=message,
            parse_mode="Markdown"
        )

    def send_favorites(self, _):
        favorites = self.postgres.get_favourites()
        if not favorites:
            return self.bot.send_message(
                chat_id=self.chat_id,
                text="You don't have any favorites yet 😢"
            )

        print(favorites)

        # for counter, favorite in enumerate(favorites, start=1):
        #     flat_obj = Flat(**favorite["flat"])
        #     flat_msg = self.flat_to_msg(flat_obj, counter)

        #     markup = types.InlineKeyboardMarkup()
        #     markup.add(
        #         types.InlineKeyboardButton(
        #             "🔍 View Link", url=flat_obj.link),
        #     )
        #     markup.add(
        #         types.InlineKeyboardButton(
        #             "❌ Remove", callback_data=f"remove_from_favorites:{flat_obj.id}"),
        #     )
        #     self.bot.send_message(
        #         chat_id=self.chat_id,
        #         text=flat_msg,
        #         parse_mode="Markdown",
        #         reply_markup=markup
        #     )
        #     time.sleep(0.5)

    def send_flat_message(self, flat: Flat, counter: str = None):
        msg_txt = self.flat_to_msg(flat, counter)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔍 View Link", url=flat.link),
        )
        markup.add(
            types.InlineKeyboardButton(
                "❤️ Add to Favorites", callback_data=f"add_to_favorites:{flat.id}"),
        )

        self.bot.send_message(
            chat_id=self.chat_id,
            text=msg_txt,
            parse_mode="Markdown",
            reply_markup=markup
        )

    def flat_to_msg(self, flat: Flat, counter: int = None) -> str:
        base_msg = (
            f"*District*: {flat.district}\n"
            f"*Street*: {flat.street}\n"
            f"*Series*: {flat.series}\n"
            f"*Rooms*: {flat.rooms}\n"
            f"*M2*: {flat.m2}\n"
            f"*Floor*: {flat.floor}/{flat.last_floor}\n"
            f"*Price per m2*: {flat.price_per_m2}\n"
            f"*Full price*: {flat.full_price}\n"
        )

        return f"#: {counter}\n" + base_msg if counter is not None else base_msg

    def _start_polling(self):
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                print(f"Error in bot polling: {e}")
                time.sleep(5)
                continue
