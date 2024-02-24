from django.apps import AppConfig
import telebot
from django.conf import settings


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    webhook = "za1hdz9yno.loclx.io"
    bot = telebot.TeleBot(settings.BOT_TOKEN)
    bot.remove_webhook()
    bot.set_webhook(webhook)

