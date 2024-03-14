import re
from tempfile import NamedTemporaryFile
from datetime import datetime as dt

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
    if request.POST:
        date = request.POST.get("daily-report-date")
        try:
            date = dt.strptime(date, "%Y-%m-%d")
        except ValueError as err:
            messages.error(request, "Не получилось скачать отчет!")
            return HttpResponse(err)

        report = ExcelDailyReport(settings.BASE_DIR / "orders/excel_templates/daily_report.xlsx", date)

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

    order = Order(owner=owner)
    if employee:
        if not employee.point:
            bot.send_message(data.from_user.id, "Вы не привязаны к точке, обратитесь к вашему руководителю")
            return
        # Проверяется, был ли сделан уже заказ сегодня
        if has_order_today(owner=owner, point=employee.point):
            bot.send_message(data.from_user.id, "Сегодня вы уже сделали заказ. Можете его редактировать")
            return

    if not owner.points.exists():
        bot.send_message(data.from_user.id, "Вы еще не добавили точки для доставки!")
        return

    # Выбор самовывоз или доставка на точку для тех, у кого включен самовывоз
    if owner.pickup:
        send = bot.send_message(data.from_user.id, "Выберите, доставить на точку или самовывоз:",
                                reply_markup=pickup_markup())
        bot.register_next_step_handler(send, process_delivery_point, order=order)
        return

    # Если самовывоз не включен, то ему нужно выбрать точку для доставки
    send = bot.send_message(data.from_user.id, "Выберите точку, на которую нужно доставить заказ:",
                            reply_markup=order_points_markup(owner.points.all()))
    bot.register_next_step_handler(send, process_delivery_point, order=order, pickup=False)
    return


def start_process_order_items(order: Order, user_id):

    products = Product.objects.all().order_by('product_type')

    # Главное сообщение с информацией о заказе
    send = bot.send_message(user_id, "Ваш новый заказ:\n")
    main_message = {"id": send.message_id, "text": send.text}

    # Генерируется сообщение для продукта с его ценой и названием
    product = products[0]
    message_text = product.generate_message(order.owner)
    send = bot.send_message(user_id, message_text, parse_mode="HTML", reply_markup=order_markup())
    product_message = {"id": send.message_id, "text": send.text}

    bot.register_next_step_handler(send, process_new_order_item, main_message=main_message,
                                   product_message=product_message, order=order,
                                   products=products, ordered_items=list())


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

            if kwargs["order"].employee:
                kwargs["order"].point = kwargs["order"].employee.point
                start_process_order_items(kwargs["order"], message.from_user.id)
                return

            send = bot.send_message(message.from_user.id, "Выберите точку, на которую нужно доставить заказ:",
                                    reply_markup=order_points_markup(kwargs["order"].owner.points.all()))
            bot.register_next_step_handler(send, process_delivery_point, **kwargs)
            return

        if message.text == "Самовывоз":
            if has_order_today(owner=kwargs["order"].owner, pickup=True):
                send = bot.send_message(message.from_user.id,
                                        "У вас уже есть заказ на самовыоз сегодня",
                                        reply_markup=pickup_markup())
                bot.register_next_step_handler(send, process_delivery_point, **kwargs)
                return
            kwargs.update({"pickup": True})
            kwargs["order"].pickup = True
            start_process_order_items(kwargs["order"], message.from_user.id)
            return

    point_address = message.text
    point = Point.objects.filter(address=point_address).first()
    if not point:
        send = bot.send_message(message.from_user.id, "Такой точки нет, выберите из предложенных вариантов:",
                                reply_markup=order_points_markup(kwargs["order"].owner.points.all()))
        bot.register_next_step_handler(send, process_delivery_point, **kwargs)
        return

    if has_order_today(owner=kwargs["order"].owner, point=point):
        send = bot.send_message(message.from_user.id, "У вас уже есть заказ сегодня на эту точку, выберите другую:",
                                reply_markup=order_points_markup(kwargs["order"].owner.points.all()))
        bot.register_next_step_handler(send, process_delivery_point, **kwargs)
        return

    kwargs["order"].point = point
    start_process_order_items(kwargs["order"], message.from_user.id)


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
        kwargs.get("ordered_items").append(OrderItem(order=kwargs["order"], product=product, count=count))

        # Вносим информацию о заказе в главное сообщение
        special_price = product.get_special_price_for_user(kwargs["order"].owner)
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

        total_items_count = 0
        for item in kwargs["ordered_items"]:
            total_items_count += item.count

        # Проверка на количество заказанной продукции
        limit = 15
        if kwargs["order"].owner.reduced_limit:
            limit = 10

        if total_items_count < limit:
            bot.send_message(message.from_user.id, f"Минимальное количетсво продукции для заказа - {limit}.\n")
            start_process_order_items(kwargs["order"], message.from_user.id)
            return

        completing_order(message, **kwargs)
        return

    # Генерируется сообщение для следующего продукта с его ценой и названием
    kwargs["products"] = kwargs["products"][1:]
    next_product = kwargs["products"][0]
    message_text = next_product.generate_message(kwargs["order"].owner)
    send = bot.send_message(message.from_user.id, message_text, parse_mode="HTML", reply_markup=order_markup())
    kwargs["product_message"] = {"id": send.message_id, "text": send.text}

    bot.register_next_step_handler(send, process_new_order_item, **kwargs)


@order_acceptance(bot=bot)
def completing_order(message: telebot.types.Message, **kwargs):
    order = kwargs["order"]
    order.save()

    for item in kwargs["ordered_items"]:
        item.save()

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
    try:
        order.update_item(product, count)
    except OrderItemsLimitError as err:
        bot.send_message(data.from_user.id, err)
    else:
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
    try:
        order.update_item(product, count)
    except OrderItemsLimitError as err:
        bot.send_message(message.from_user.id, err)
    else:
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

    try:
        order.delete_item(product)
    except OrderItemsLimitError as err:
        bot.send_message(data.from_user.id, err)
    else:
        order_info = order.generate_message()

        bot.edit_message_text(order_info, data.from_user.id, data.message.id, parse_mode="HTML",
                              reply_markup=order_products_markup(order_id))


bot.add_custom_filter(IsOwner())
bot.add_custom_filter(IsRegistered())
