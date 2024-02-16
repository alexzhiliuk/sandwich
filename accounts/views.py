import re

import telebot
from telebot import custom_filters

from .models import *
from django.db.utils import IntegrityError
from .filters import IsOwner
from .markups import *

from bot.apps import BotConfig

bot = BotConfig.bot

BOT_URL = "t.me/sandwich_order_test_bot"


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
    bot.edit_message_text("Ваши точки:", message.from_user.id, message_id, reply_markup=points_markup(
        Owner.objects.get(tg_id=user_id).points.all().values("id", "address")))
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
        f"{data.message.text}. Удалить?\n<b>Все сотрудники, привязанные к данной точке, будут отвязаны</b>",
        data.from_user.id,
        data.message.id,
        reply_markup=confirm_markup(
            {"text": "Удалить", "callback": f"confirm_{data.data}"},
            {"text": "Отмена", "callback": f"{data.data.replace('_delete', '')}"}
        ),
        parse_mode="HTML"
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


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"staff", data.data))
@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"back_staff", data.data))
def owner_staff(data: telebot.types.CallbackQuery):
    user_id = data.from_user.id
    staff = Owner.objects.get(tg_id=user_id).staff.all().values("id", "fio")

    if data.data.startswith("back"):
        bot.edit_message_text(
            "Ваши сотрудники:",
            data.from_user.id,
            data.message.id,
            reply_markup=staff_markup(staff)
        )
    else:
        bot.send_message(data.from_user.id, "Ваши сотрудники:", reply_markup=staff_markup(staff))


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"add_employee", data.data))
def add_employee(data: telebot.types.CallbackQuery):
    user_id = data.from_user.id
    reg_link = BOT_URL + f"?start={user_id}"

    bot.send_message(data.from_user.id,
                     f"Для регистрации сотрудник должен перейти по данной ссылке:\n<b>{reg_link}</b>",
                     parse_mode="HTML")


def process_employee_fio(message: telebot.types.Message, owner):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_employee_fio, owner)
        return

    fio = message.text

    send = bot.send_message(message.chat.id, "Введите номер телефона (не используйте +, - и скобочки):")
    bot.register_next_step_handler(send, process_employee_phone, owner, fio)


def process_employee_phone(message: telebot.types.Message, owner, fio: str):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_employee_phone, owner, fio)
        return

    phone = message.text.replace(" ", "")

    if not phone.isnumeric():
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только цифры (без  +, - и скобочек)!")
        bot.register_next_step_handler(send, process_employee_phone, owner, fio)
        return

    try:
        Employee.objects.create(owner=owner, fio=fio, tg_id=message.chat.id, phone=phone, is_active=True)
    except IntegrityError:
        bot.send_message(
            message.chat.id,
            "Аккаунт с такими данными уже зарегистрирован, попробуйте снова или обратитесь к администратору"
        )
    else:
        bot.send_message(message.chat.id, "Регистрация завершена!")


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"employee_\d+", data.data))
def owner_employee(data: telebot.types.CallbackQuery):
    employee_id = int(data.data.split("_")[-1])
    employee = Employee.objects.filter(id=employee_id).select_related("point").first()

    if not employee:
        bot.send_message(data.from_user.id, "Данного сотрудника не существует")
        return

    bot.edit_message_text(
        f"Сотрудник {employee.fio}\nТочка: {employee.point.address if employee.point else 'нет точки'}",
        data.from_user.id,
        data.message.id,
        reply_markup=employee_markup(employee)
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"employee_\d+_point", data.data))
def owner_employee_point_choice(data: telebot.types.CallbackQuery):
    employee_id = int(data.data.split("_")[1])
    employee = Employee.objects.filter(id=employee_id).select_related("point").first()

    if not employee:
        bot.send_message(data.from_user.id, "Данного сотрудника не существует")
        return

    bot.edit_message_text(
        f"Сотрудник {employee.fio}\nВыберите новую точку:",
        data.from_user.id,
        data.message.id,
        reply_markup=points_markup(Point.objects.filter(owner__tg_id=data.from_user.id).values("id", "address"),
                                   employee)
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"employee_\d+_point_\d+", data.data))
def owner_employee_set_point(data: telebot.types.CallbackQuery):
    employee_id = int(data.data.split("_")[1])
    employee = Employee.objects.filter(id=employee_id).first()
    if not employee:
        bot.send_message(data.from_user.id, "Данного сотрудника не существует")
        return

    point_id = int(data.data.split("_")[-1])
    if point_id == 0:
        employee.unset_point()
        bot.send_message(data.from_user.id, "Сотрудник откреплен от точки!")
    else:
        point = Point.objects.filter(id=point_id).first()

        if not point:
            bot.send_message(data.from_user.id, "Данной точки не существует")
            return

        employee.set_point(point)
        bot.send_message(data.from_user.id, "Сотруднику назначена новая точка!")

    bot.edit_message_text(
        f"Сотрудник {employee.fio}\nТочка: {employee.point.address if employee.point else 'нет точки'}",
        data.from_user.id,
        data.message.id,
        reply_markup=employee_markup(employee)
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"employee_delete_\d+", data.data))
def delete_employee(data: telebot.types.CallbackQuery):
    bot.edit_message_text(
        f"{data.message.text}\n Удалить сотрудника?",
        data.from_user.id,
        data.message.id,
        reply_markup=confirm_markup(
            {"text": "Удалить", "callback": f"confirm_{data.data}"},
            {"text": "Отмена", "callback": f"{data.data.replace('_delete', '')}"}
        )
    )


@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"confirm_employee_delete_\d+", data.data))
def confirm_delete_employee(data: telebot.types.CallbackQuery):
    employee_id = int(data.data.split("_")[-1])
    employee = Employee.objects.filter(id=employee_id).first()

    if not employee:
        bot.send_message(data.from_user.id, "Данной точки не существует")
        return

    fio = employee.fio
    employee.delete()
    bot.send_message(data.from_user.id, f"Сотрудник {fio} удален!")

    staff = Owner.objects.get(tg_id=data.from_user.id).staff.all().values("id", "fio")
    bot.edit_message_text(
        "Ваши сотрудники:",
        data.from_user.id,
        data.message.id,
        reply_markup=staff_markup(staff)
    )


bot.add_custom_filter(IsOwner())
