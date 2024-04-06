from datetime import datetime as dt

from functools import wraps

from telebot.types import CallbackQuery, Message
from telebot import TeleBot
from telebot.types import ReplyKeyboardRemove


def cancel(bot: TeleBot, cancel_message=None):
    def decorator(function):
        @wraps(function)
        def wrap(message: Message, *args, **kwargs):
            if message.text == "/cancel" or message.text.lower() == "отмена":
                bot.send_message(message.from_user.id, cancel_message or "Операция отменена",
                                 reply_markup=ReplyKeyboardRemove())
            else:
                return function(message, *args, **kwargs)

        return wrap

    return decorator
