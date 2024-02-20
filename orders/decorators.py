from functools import wraps

from telebot.types import CallbackQuery
from telebot import TeleBot

from .utils import time_access


def order_edit_time(bot: TeleBot):
    def decorator(function):
        @wraps(function)
        def wrap(data: CallbackQuery, *args, **kwargs):
            if time_access(16, 45):
                return function(data, *args, **kwargs)
            else:
                bot.send_message(data.from_user.id, "Уже слишком поздно")

        return wrap

    return decorator
