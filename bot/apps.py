import os
from time import sleep

from django.apps import AppConfig
import telebot
from django.conf import settings


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    bot = telebot.TeleBot(token=settings.BOT_TOKEN)
    webhook = os.getenv("WEBHOOK", "u9wppkrfzp.loclx.io")

    def ready(self):
        self.bot.remove_webhook()
        sleep(1)
        self.bot.set_webhook(self.webhook)

