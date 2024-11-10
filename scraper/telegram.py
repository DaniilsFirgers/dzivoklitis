import time
import telebot
from telebot import types

from scraper.flat import Flat
from scraper.database import FlatsTinyDb
from threading import Thread


class TelegramBot:
    def __init__(self, token, chat_id, tiny_db: FlatsTinyDb):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        self.tiny_db = tiny_db

        self.bot.callback_query_handler(func=lambda call: call.data.startswith(
            "add_to_favorites:"))(self.handle_add_to_favorites)
        self.bot.message_handler(commands=["favorites"])(self.send_favorites)
        Thread(target=self.start_polling, daemon=True).start()

    def handle_add_to_favorites(self, call):
        id = call.data.split(":")[1]
        if self.tiny_db.exists(id, "favorites"):
            return self.bot.answer_callback_query(
                call.id, "This flat is already in your favorites list ✅")

        flat = self.tiny_db.get(id, "parsed")
        self.tiny_db.insert(id, flat["flat"], "favorites")
        self.bot.answer_callback_query(
            call.id, "Flat added to favorites ❤️"
        )

    def send_message(self, message: str):
        self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode="Markdown"
        )

    def send_favorites(self, _):
        favorites = self.tiny_db.favorites_db.all()
        if not favorites:
            return self.bot.send_message(
                chat_id=self.chat_id,
                text="You don't have any favorites yet 😢"
            )

        for counter, favorite in enumerate(favorites, start=1):
            flat_obj = Flat(**favorite["flat"])
            flat_msg = self.flat_to_msg(flat_obj, counter)
            self.bot.send_message(
                chat_id=self.chat_id,
                text=flat_msg,
                parse_mode="Markdown"
            )
            time.sleep(0.5)

    def send_flat_message(self, flat: Flat, counter: str):
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

    def start_polling(self):
        self.bot.polling()
