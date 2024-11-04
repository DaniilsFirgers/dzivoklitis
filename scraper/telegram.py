import telebot
from telebot import types
from scraper.main import Flat


class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id

    def send_message(self, flat: Flat):
        pass
