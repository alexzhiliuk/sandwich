from django.apps import AppConfig
import telebot
from django.conf import settings


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'
    webhook = "tgr835hvdf.loclx.io"
    bot = telebot.TeleBot(settings.BOT_TOKEN)

    def ready(self):

        self.bot.remove_webhook()
        self.bot.set_webhook(self.webhook)

