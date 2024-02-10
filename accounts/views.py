import re

import telebot
from .models import *
from bot.views import bot
from django.db.utils import IntegrityError
from .filters import IsOwner
from .markups import *


@bot.message_handler(commands=['reg'])
def registration(message: telebot.types.Message):

    user_id = message.chat.id

    if Owner.objects.filter(tg_id=user_id).exists() or Employee.objects.filter(tg_id=user_id).exists():
        bot.send_message(user_id, 'Вы уже зарегистрированы в системе!')
        return

    send = bot.send_message(user_id, "Для начала регистрации введите УНП:")
    bot.register_next_step_handler(send, process_unp)


def process_unp(message: telebot.types.Message):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_unp)
        return

    if not message.text.isnumeric():
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только цифры!")
        bot.register_next_step_handler(send, process_unp)
        return

    unp = message.text

    send = bot.send_message(message.chat.id, "Введите ФИО:")
    bot.register_next_step_handler(send, process_fio, unp)


def process_fio(message: telebot.types.Message, unp: str):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_fio, unp)
        return

    fio = message.text

    send = bot.send_message(message.chat.id, "Введите номер телефона (не используйте +, - и скобочки):")
    bot.register_next_step_handler(send, process_phone, unp, fio)


def process_phone(message: telebot.types.Message, unp: str, fio: str):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_phone, unp, fio)
        return

    phone = message.text.replace(" ", "")

    if not phone.isnumeric():
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только цифры (без  +, - и скобочек)!")
        bot.register_next_step_handler(send, process_phone, unp, fio)
        return

    try:
        Owner.objects.create(unp=unp, fio=fio, tg_id=message.chat.id, phone=phone)
    except IntegrityError:
        bot.send_message(
            message.chat.id,
            "Аккаунт с такими данными уже зарегистрирован, попробуйте снова или обратитесь к администратору"
        )
    else:
        bot.send_message(message.chat.id, "Регистрация завершена! Ожидайте пока администратор подтвердит регистрацию")


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"add_point", data.data))
def adding_point(data: telebot.types.CallbackQuery):

    send = bot.send_message(data.from_user.id, "Введите адрес новой точки")
    bot.register_next_step_handler(send, process_point_address, data.message.id)


def process_point_address(message: telebot.types.Message, message_id):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_point_address)
        return

    user_id = message.chat.id
    Point.objects.create(
        owner=Owner.objects.get(tg_id=user_id),
        address=message.text
    )
    bot.edit_message_text("Ваши точки:", message.from_user.id, message_id, reply_markup=points_markup(Owner.objects.get(tg_id=user_id).points.all().values("id", "address")))
    bot.send_message(user_id, f"Точка с адресом <b>{message.text}</b> добавлена!", parse_mode="HTML")


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"points", data.data))
@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"back_points", data.data))
def owner_points(data: telebot.types.CallbackQuery):

    user_id = data.from_user.id
    points = Owner.objects.get(tg_id=user_id).points.all().values("id", "address")

    if data.data.startswith("back"):
        bot.edit_message_text(
            "Ваши точки:",
            data.from_user.id,
            data.message.id,
            reply_markup=points_markup(points)
        )
    else:
        bot.send_message(data.from_user.id, "Ваши точки:", reply_markup=points_markup(points))


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"point_\d+", data.data))
def owner_point(data: telebot.types.CallbackQuery):

    point_id = int(data.data.split("_")[-1])
    point = Point.objects.filter(id=point_id).first()

    if not point:
        bot.send_message(data.from_user.id, "Данной точки не существует")
        return

    bot.edit_message_text(
        f"Точка {point.address}",
        data.from_user.id,
        data.message.id,
        reply_markup=point_markup(point)
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"point_edit_\d+", data.data))
def edit_point(data: telebot.types.CallbackQuery):

    point_id = int(data.data.split("_")[-1])
    point = Point.objects.filter(id=point_id).first()

    if not point:
        bot.send_message(data.from_user.id, "Данной точки не существует")
        return

    send = bot.send_message(data.from_user.id, "Введите новый адрес точки:")
    bot.register_next_step_handler(send, process_editing_point, data.message.id, point)


def process_editing_point(message: telebot.types.Message, message_id, point):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_editing_point, message_id, point)
        return

    new_address = message.text
    point.address = new_address
    point.save()

    bot.edit_message_text(new_address, message.from_user.id, message_id, reply_markup=point_markup(point))
    bot.send_message(message.from_user.id, "Адрес точки изменен!")


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"point_delete_\d+", data.data))
def delete_point(data: telebot.types.CallbackQuery):

    bot.edit_message_text(
        f"{data.message.text}. Удалить?",
        data.from_user.id,
        data.message.id,
        reply_markup=confirm_markup(
            {"text": "Удалить", "callback": f"confirm_{data.data}"},
            {"text": "Отмена", "callback": f"{data.data.replace('_delete', '')}"}
        )
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"confirm_point_delete_\d+", data.data))
def confirm_delete_point(data: telebot.types.CallbackQuery):

    point_id = int(data.data.split("_")[-1])
    point = Point.objects.filter(id=point_id).first()

    if not point:
        bot.send_message(data.from_user.id, "Данной точки не существует")
        return

    address = point.address
    point.delete()
    bot.send_message(data.from_user.id, f"Точка {address} удалена!")

    points = Owner.objects.get(tg_id=data.from_user.id).points.all().values("id", "address")
    bot.edit_message_text(
        "Ваши точки:",
        data.from_user.id,
        data.message.id,
        reply_markup=points_markup(points)
    )


bot.add_custom_filter(IsOwner())
#  t.me/sandwich_order_test_bot?start=1234567