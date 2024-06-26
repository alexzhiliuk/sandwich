from datetime import datetime as dt

from functools import wraps

from telebot.types import CallbackQuery
from telebot import TeleBot

from .models import OrderAcceptance
from .utils import time_access


def order_edit_time(bot: TeleBot):
    def decorator(function):
        @wraps(function)
        def wrap(data: CallbackQuery, *args, **kwargs):
            weekday = dt.now().weekday()
            if weekday in [0, 1, 2, 3]:
                access = time_access(16, 45)
            elif weekday == 6:
                access = time_access(14, 0)
            else:
                # в пт-сб редактировать можно в любое время
                access = True

            if access:
                return function(data, *args, **kwargs)
            else:
                bot.send_message(data.from_user.id, "Редактировать заявки можно до 16:45 с понедельника по четверг"
                                                    " и до 14:00 в воскресенье")

        return wrap

    return decorator


def order_acceptance(bot: TeleBot):
    def decorator(function):
        @wraps(function)
        def wrap(data: CallbackQuery, *args, **kwargs):
            if OrderAcceptance.objects.first().status == OrderAcceptance.Status.OPEN:
                return function(data, *args, **kwargs)
            else:
                bot.send_message(data.from_user.id, "Прием заявок осуществляется с понедельника "
                                                    "по четверг до 17:00, в воскресенье до 15:00")

        return wrap

    return decorator
