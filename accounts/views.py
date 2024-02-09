import telebot
from .models import *
from bot.views import bot
from django.db.utils import IntegrityError


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
