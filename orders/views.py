import re
from tempfile import NamedTemporaryFile

import telebot
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect

from accounts.filters import IsOwner, IsRegistered
from accounts.utils import get_owner_by_id
from .decorators import order_edit_time, order_acceptance
from .excel import ExcelDailyReport

from .models import *
from .markups import *
from .utils import has_order_today

from telebot.types import ReplyKeyboardRemove

from bot.apps import BotConfig

bot = BotConfig.bot


def close_acceptance(request):
    OrderAcceptance.objects.update(status=OrderAcceptance.Status.CLOSE)
    Order.accept_created()
    messages.success(request, "Прием заявок закрыт!")
    return redirect(request.META.get("HTTP_REFERER"))


def daily_report(request):
    report = ExcelDailyReport(settings.BASE_DIR / "excel_templates/daily_report.xlsx")

    with NamedTemporaryFile() as tmp:
        report.wb.save(tmp.name)
        tmp.seek(0)
        stream = tmp.read()

    response = HttpResponse(content=stream, content_type='application/ms-excel', )
    response['Content-Disposition'] = f'attachment; filename=report.xlsx'
    return response


@bot.message_handler(commands=["new_order"])
@bot.callback_query_handler(func=lambda data: re.fullmatch(r"new_order", data.data))
@order_acceptance(bot=bot)
def new_order(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию + определение владельца (нужно для спеццены)
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return
    if employee:
        if not employee.point:
            bot.send_message(data.from_user.id, "Вы не привязаны к точке, обратитесь к вашему руководителю")
            return
        # Проверяется, был ли сделан уже заказ сегодня
        if has_order_today(employee=employee):
            bot.send_message(data.from_user.id, "Сегодня вы уже сделали заказ. Можете его редактировать")
            return

    if not owner.points.exists():
        bot.send_message(data.from_user.id, "Вы еще не добавили точки для доставки!")
        return

    products = Product.objects.all().order_by('product_type')

    # Главное сообщение с информацией о заказе
    send = bot.send_message(data.from_user.id, "Ваш новый заказ:\n")
    main_message = {"id": send.message_id, "text": send.text}

    # Генерируется сообщение для продукта с его ценой и названием
    product = products[0]
    message_text = product.generate_message(owner)
    send = bot.send_message(data.from_user.id, message_text, parse_mode="HTML", reply_markup=order_markup())
    product_message = {"id": send.message_id, "text": send.text}

    bot.register_next_step_handler(send, process_new_order_item, main_message=main_message,
                                   product_message=product_message, owner=owner, employee=employee,
                                   products=products, ordered_items=dict())


def process_new_order_item(message: telebot.types.Message, **kwargs):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_new_order_item, **kwargs)
        return

    if not message.text.isnumeric() and message.text not in ["Пропустить", "Отмена", "Доставить на точку", "Самовывоз"]:
        send = bot.send_message(message.from_user.id,
                                "Сообщение должно содержать только цифры либо 'Пропустить' и 'Отмена'!")
        bot.register_next_step_handler(send, process_new_order_item, **kwargs)
        return

    if message.text == "Отмена":
        bot.send_message(message.from_user.id, "Заказ отменен!", reply_markup=ReplyKeyboardRemove())
        return

    elif message.text.isnumeric():
        product = kwargs["products"][0]
        count = int(message.text)

        # Добавляем информацию о заказанной продукции
        kwargs.get("ordered_items").update({
            product: count
        })

        # Вносим информацию о заказе в главное сообщение
        special_price = product.get_special_price_for_user(kwargs["owner"])
        price = special_price.price * count if special_price else product.price * count
        kwargs["main_message"]["text"] += f"\n   - {product.name} {count} шт. <i>{round(price, 2)} руб.</i>"
        bot.edit_message_text(
            kwargs["main_message"]["text"],
            message.from_user.id,
            kwargs["main_message"]["id"],
            parse_mode="HTML"
        )

    # Очищаем переписку
    bot.delete_messages(message.from_user.id, [kwargs["product_message"]["id"], message.message_id])

    # Завершаем оформление заказа
    if len(kwargs["products"]) == 1:
        if len(kwargs["ordered_items"]) == 0:
            bot.send_message(message.from_user.id, "Ваш заказ пуст!", reply_markup=ReplyKeyboardRemove())
            return

        # Выбор самовывоз или доставка на точку для тех, у кого включен самовывоз
        if kwargs["owner"].pickup:
            send = bot.send_message(message.from_user.id, "Выберите, доставить на точку или самовывоз:",
                                    reply_markup=pickup_markup())
            bot.register_next_step_handler(send, process_delivery_point, **kwargs)
            return

        kwargs["pickup"] = False
        # Если заказывает владелец, то ему нужно выбрать точку для доставки
        if not kwargs["employee"]:
            send = bot.send_message(message.from_user.id, "Выберите точку, на которую нужно доставить заказ:",
                                    reply_markup=order_points_markup(kwargs["owner"].points.all()))
            bot.register_next_step_handler(send, process_delivery_point, **kwargs)
            return

        kwargs["point"] = kwargs["employee"].point
        completing_order(message, **kwargs)
        return

    # Генерируется сообщение для следующего продукта с его ценой и названием
    kwargs["products"] = kwargs["products"][1:]
    next_product = kwargs["products"][0]
    message_text = next_product.generate_message(kwargs["owner"])
    send = bot.send_message(message.from_user.id, message_text, parse_mode="HTML", reply_markup=order_markup())
    kwargs["product_message"] = {"id": send.message_id, "text": send.text}

    bot.register_next_step_handler(send, process_new_order_item, **kwargs)


def process_delivery_point(message: telebot.types.Message, **kwargs):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_delivery_point, **kwargs)
        return

    if message.text == "Отмена":
        bot.send_message(message.from_user.id, "Заказ отменен", reply_markup=ReplyKeyboardRemove())
        return

    if kwargs.get("pickup") is None:

        if message.text not in ["Доставить на точку", "Самовывоз"]:
            send = bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой!")
            bot.register_next_step_handler(send, process_delivery_point, **kwargs)
            return

        if message.text == "Доставить на точку":
            kwargs.update({"pickup": False})

            if kwargs["employee"]:
                kwargs["point"] = kwargs["employee"].point
                completing_order(message, **kwargs)
                return

            send = bot.send_message(message.from_user.id, "Выберите точку, на которую нужно доставить заказ:",
                                    reply_markup=order_points_markup(kwargs["owner"].points.all()))
            bot.register_next_step_handler(send, process_delivery_point, **kwargs)
            return

        if message.text == "Самовывоз":
            if has_order_today(owner=kwargs["owner"], pickup=True):
                send = bot.send_message(message.from_user.id,
                                        "У вас уже есть заказ на самовыоз сегодня",
                                        reply_markup=pickup_markup())
                bot.register_next_step_handler(send, process_delivery_point, **kwargs)
                return
            kwargs.update({"pickup": True})
            completing_order(message, **kwargs)
            return

    point_address = message.text
    point = Point.objects.filter(address=point_address).first()
    if not point:
        send = bot.send_message(message.from_user.id, "Такой точки нет, выберите из предложенных вариантов:",
                                reply_markup=order_points_markup(kwargs["owner"].points.all()))
        bot.register_next_step_handler(send, process_delivery_point, **kwargs)
        return

    if has_order_today(owner=kwargs["owner"], point=point):
        send = bot.send_message(message.from_user.id, "У вас уже есть заказ сегодня на эту точку, выберите другую:",
                                reply_markup=order_points_markup(kwargs["owner"].points.all()))
        bot.register_next_step_handler(send, process_delivery_point, **kwargs)
        return

    kwargs["point"] = point
    completing_order(message, **kwargs)


@order_acceptance(bot=bot)
def completing_order(message: telebot.types.Message, **kwargs):
    if kwargs["employee"]:
        if kwargs.get("pickup"):
            order = Order.objects.create(owner=kwargs["owner"], employee=kwargs["employee"], pickup=True)
        else:
            order = Order.objects.create(owner=kwargs["owner"], employee=kwargs["employee"], point=kwargs["point"])
    else:
        if kwargs.get("pickup"):
            order = Order.objects.create(owner=kwargs["owner"], pickup=True)
        else:
            order = Order.objects.create(owner=kwargs["owner"], point=kwargs["point"])

    order.fill(kwargs["ordered_items"])

    final_message = (f"Ваш заказ принят!\nИтоговая сумма заказа: {order.get_final_info()[1]} руб."
                     f"\n{'Самовывоз' if order.pickup else f'Достака на точку: {order.point.address}'}"),
    bot.send_message(message.from_user.id, final_message, reply_markup=ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order", data.data))
@order_edit_time(bot=bot)
def update_order(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return
    if employee:
        orders = Order.objects.filter(status=Order.Status.CREATED, employee=employee)
        # ...
        return

    orders = Order.objects.filter(status=Order.Status.CREATED, owner=owner, employee=None).values("id", "created_at")
    if not orders:
        bot.send_message(data.from_user.id, "У вас нет заказов, которые можно редактировать")
        return

    if "меню:" in data.message.text.lower():
        bot.send_message(data.from_user.id, "Выберите заказ, который хотите редактировать:",
                         reply_markup=orders_markup(orders))
    else:
        bot.edit_message_text("Выберите заказ, который хотите редактировать:", data.from_user.id, data.message.id,
                              reply_markup=orders_markup(orders))


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+", data.data))
@order_edit_time(bot=bot)
def select_product(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[-1])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    order_info = order.generate_message()

    bot.edit_message_text(order_info, data.from_user.id, data.message.id, parse_mode="HTML",
                          reply_markup=order_products_markup(order_id))


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+_page_\d+", data.data))
@order_edit_time(bot=bot)
def select_product_change_page(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[2])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    page = int(data.data.split("_")[-1])
    bot.edit_message_text(data.message.text, data.from_user.id, data.message.id,
                          reply_markup=order_products_markup(order_id, page))


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+_product_\d+", data.data))
@order_edit_time(bot=bot)
def select_product_count(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[2])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    product_id = int(data.data.split("_")[-1])
    product = Product.objects.filter(id=product_id).first()
    if not product:
        bot.send_message(data.from_user.id, "Такого продукта не существует!")
        return

    bot.edit_message_text(product.generate_message(owner), data.from_user.id, data.message.id,
                          reply_markup=order_products_count_markup(order_id, product_id),
                          parse_mode="HTML")


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+_product_\d+_count_\d+", data.data))
@order_edit_time(bot=bot)
def update_order_product(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[2])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    product_id = int(data.data.split("_")[4])
    product = Product.objects.filter(id=product_id).first()
    if not product:
        bot.send_message(data.from_user.id, "Такого продукта не существует!")
        return

    count = int(data.data.split("_")[-1])
    order.update_item(product, count)

    order_info = order.generate_message()

    bot.edit_message_text(order_info, data.from_user.id, data.message.id,
                          reply_markup=order_products_markup(order_id),
                          parse_mode="HTML")


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+_product_\d+_count", data.data))
@order_edit_time(bot=bot)
def get_new_product_count(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[2])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    product_id = int(data.data.split("_")[4])
    product = Product.objects.filter(id=product_id).first()
    if not product:
        bot.send_message(data.from_user.id, "Такого продукта не существует!")
        return

    send = bot.send_message(data.from_user.id, "Введите количество:")
    bot.register_next_step_handler(send, process_new_product_count, order, product, data.message.id)


def process_new_product_count(message: telebot.types.Message, order, product, message_id):
    if message.content_type != "text":
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только текст!")
        bot.register_next_step_handler(send, process_new_product_count, order, product)
        return

    if not message.text.isnumeric():
        send = bot.send_message(message.from_user.id, "Сообщение должно содержать только цифры!")
        bot.register_next_step_handler(send, process_new_product_count, order, product)
        return

    count = int(message.text)
    order.update_item(product, count)

    order_info = order.generate_message()

    bot.edit_message_text(order_info, message.from_user.id, message_id,
                          reply_markup=order_products_markup(order.id),
                          parse_mode="HTML")


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"update_order_\d+_product_\d+_delete", data.data))
@order_edit_time(bot=bot)
def delete_order_product(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
        bot.send_message(data.from_user.id, "Вы не заргеистрированы")
        return

    order_id = int(data.data.split("_")[2])
    order = Order.objects.filter(id=order_id).first()
    if not order:
        bot.send_message(data.from_user.id, "Такого заказа не существует!")
        return

    product_id = int(data.data.split("_")[4])
    product = Product.objects.filter(id=product_id).first()
    if not product:
        bot.send_message(data.from_user.id, "Такого продукта не существует!")
        return

    order.delete_item(product)

    order_info = order.generate_message()

    bot.edit_message_text(order_info, data.from_user.id, data.message.id, parse_mode="HTML",
                          reply_markup=order_products_markup(order_id))


bot.add_custom_filter(IsOwner())
bot.add_custom_filter(IsRegistered())
