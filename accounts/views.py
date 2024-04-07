import re

import telebot
from django.contrib import messages
from django.shortcuts import redirect
from telebot.types import ReplyKeyboardRemove

from .exceptions import NewUserPhoneNumberError
from .models import *
from django.db.utils import IntegrityError
from .filters import IsOwner
from .markups import *
from .excel import ExcelRegistrateUsers

from bot.apps import BotConfig
from bot.decorators import cancel
from .utils import create_phone_number_from_message

bot = BotConfig.bot

BOT_URL = "t.me/sandwich_order_test_bot"


def add_users_from_excel(request):
    if request.POST:
        file = request.FILES.get("users")
        users = ExcelRegistrateUsers(file)
        users.register()
        messages.success(request, "Новые пользователи созданы!")

    return redirect(request.META.get("HTTP_REFERER"))


@bot.message_handler(commands=['reg'])
def registration(message: telebot.types.Message):
    user_id = message.chat.id

    if Owner.objects.filter(tg_id=user_id).exists() or Employee.objects.filter(tg_id=user_id).exists():
        bot.send_message(user_id, 'Вы уже зарегистрированы в системе!')
        return

    send = bot.send_message(user_id, "Введите ваш УНП:")
    bot.register_next_step_handler(send, process_unp)


@cancel(bot=bot)
def process_unp(message: telebot.types.Message):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_unp)
        return

    unp = message.text

    owner = Owner.objects.filter(unp=unp).first()
    if not owner:
        send = bot.send_message(message.from_user.id,
                                "Такой УНП не зарегистрирован, попробуйте еще раз или обратитесь к администратору")
        bot.register_next_step_handler(send, process_unp)
        return

    # Если сотрудник попытается зарегистрировать через УНП
    if owner.tg_id:
        bot.send_message(message.from_user.id,
                         "Пользователь с таким УНП уже зарегистрирован. Если вы хотите зарегистрироваться как сотрудник, то попросите у владельца прислать вам специальную ссылку для регистрации")
        return

    send = bot.send_message(message.from_user.id, "Введите пароль:")
    bot.register_next_step_handler(send, process_password, owner)


@cancel(bot=bot)
def process_password(message: telebot.types.Message, owner):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_password, owner)
        return

    password = message.text

    if owner.reg_pass != password:
        send = bot.send_message(message.from_user.id, "Неверный пароль, попробуйте еще раз")
        bot.register_next_step_handler(send, process_password, owner)
        return

    owner.tg_id = message.from_user.id
    owner.save()

    bot.send_message(message.chat.id, "Регистрация завершена! Теперь Вы можете создавать заказы и управлять своими "
                                      "точками и сотрудниками")



@bot.callback_query_handler(is_owner=True, func=lambda data: re.fullmatch(r"add_point", data.data))
def adding_point(data: telebot.types.CallbackQuery):
    send = bot.send_message(data.from_user.id, "Введите адрес новой точки")
    bot.register_next_step_handler(send, process_point_address, data.message.id)


def process_point_address(message: telebot.types.Message, message_id):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_point_address, message_id)
        return

    address = message.text
    send = bot.send_message(message.from_user.id, "Введите время работы точки")
    bot.register_next_step_handler(send, process_point_working_hours, message_id, address)


def process_point_working_hours(message: telebot.types.Message, message_id, address):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_point_working_hours, message_id, address)
        return

    user_id = message.chat.id
    try:
        Point.objects.create(
            owner=Owner.objects.get(tg_id=user_id),
            address=address,
            working_hours=message.text
        )
    except IntegrityError:
        bot.send_message(
            message.chat.id,
            "Точка с таким адресом уже существует! Попробуйте снова"
        )
        return

    bot.edit_message_text("Ваши точки:", message.from_user.id, message_id, reply_markup=points_markup(
        Owner.objects.get(tg_id=user_id).points.all().values("id", "address")))
    bot.send_message(user_id, f"Точка с адресом <b>{address}</b> добавлена!", parse_mode="HTML")


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
    bot.register_next_step_handler(send, process_editing_point_address, data.message.id, point)


def process_editing_point_address(message: telebot.types.Message, message_id, point):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_editing_point_address, message_id, point)
        return

    new_address = message.text

    send = bot.send_message(message.from_user.id, "Введите новое время работы:")
    bot.register_next_step_handler(send, process_editing_point_working_hours, message_id, point, new_address)


def process_editing_point_working_hours(message: telebot.types.Message, message_id, point, new_address):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_editing_point_working_hours, message_id, point, new_address)
        return

    new_working_hours = message.text
    point.address = new_address
    point.working_hours = new_working_hours

    try:
        point.save()
    except IntegrityError:
        bot.send_message(
            message.chat.id,
            "Точка с таким адресом уже существует! Попробуйте снова"
        )
        return

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


@cancel(bot=bot, cancel_message="Регистрация отменена")
def process_employee_phone(message: telebot.types.Message, owner):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_employee_phone, owner)
        return

    try:
        phone = create_phone_number_from_message(message.text)
    except NewUserPhoneNumberError:
        send = bot.send_message(message.from_user.id, "Введеный номер телефона слишком короткий. "
                                                      "Номер телефона должен содержать 9 цифр")
        bot.register_next_step_handler(send, process_employee_phone, owner)
        return

    send = bot.send_message(message.from_user.id, f"Это верный номер? <b>{phone}</b>", parse_mode="HTML",
                            reply_markup=confirm_phone_markup())
    bot.register_next_step_handler(send, confirm_employee_phone, owner, phone)


@cancel(bot=bot, cancel_message="Регистрация отменена")
def confirm_employee_phone(message: telebot.types.Message, owner, phone):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать 'Да' либо 'Нет'")
        bot.register_next_step_handler(send, confirm_employee_phone, owner, phone, reply_markup=confirm_phone_markup())
        return

    if message.text.lower() == "да":
        send = bot.send_message(message.from_user.id, "Введите Ваше ФИО:", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(send, process_employee_fio, owner, phone)
        return

    send = bot.send_message(message.from_user.id, "Введите номер телефона еще раз:", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(send, process_employee_phone, owner)


@cancel(bot=bot, cancel_message="Регистрация отменена")
def process_employee_fio(message: telebot.types.Message, owner, phone):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_employee_fio, owner)
        return

    fio = message.text

    try:
        Employee.objects.create(owner=owner, fio=fio, tg_id=message.from_user.id, phone=phone, is_active=True)
    except IntegrityError:
        bot.send_message(
            message.chat.id,
            "Аккаунт с такими данными уже зарегистрирован, попробуйте снова или обратитесь к администратору"
        )
    else:
        bot.send_message(message.chat.id, "Регистрация завершена! Сообщите об этом своему руководителю. После того, "
                                          "как он добавит Вас к точке, Вы сможете создавать новые заказы. Вот команды, "
                                          "которые Вам понадабятся для этого:\n\n/new_order - Создать новый заказ\n"
                                          "/edit_order - Редактировать заказ")


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
