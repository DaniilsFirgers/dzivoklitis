import telebot
from telebot import types

from scraper.flat import Flat


class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id

    def send_message(self, flat: Flat):
        msg_txt = (
            f"*District*: {flat.district}\n"
            f"*Street*: {flat.street}\n"
            f"*Series*: {flat.series}\n"
            f"*Rooms*: {flat.rooms}\n"
            f"*M2*: {flat.m2}\n"
            f"*Floor*: {flat.floor}\n"
            f"*Price per m2*: {flat.price_per_m2}\n"
            f"*Full price*: {flat.full_price}\n"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔍 View Link", url=flat.link),
        )

        self.bot.send_message(
            chat_id=self.chat_id,
            text=msg_txt,
            parse_mode="Markdown",
            reply_markup=markup
        )
