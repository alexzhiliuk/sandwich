from datetime import datetime as dt

from functools import wraps

from telebot.types import CallbackQuery, Message
from telebot import TeleBot


def cancel(bot: TeleBot):
    def decorator(function):
        @wraps(function)
        def wrap(message: Message, *args, **kwargs):
            if message.text == "/cancel" or message.text.lower() == "отмена":
                bot.send_message(message.from_user.id, "Операция отменена")
            else:
                return function(message, *args, **kwargs)

        return wrap

    return decorator


