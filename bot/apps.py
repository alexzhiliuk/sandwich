from django.apps import AppConfig
import telebot
from django.conf import settings
from telebot.storage import StateMemoryStorage


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    webhook = "qjrq6udtze.loclx.io"
    bot = telebot.TeleBot(settings.BOT_TOKEN)
    bot.remove_webhook()
    bot.set_webhook(webhook)

