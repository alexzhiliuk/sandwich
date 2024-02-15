import re

import telebot
from .models import *
from bot.views import bot
from accounts.filters import IsOwner, IsRegistered
from accounts.utils import get_owner_by_id
from .markups import *

from telebot.types import ReplyKeyboardRemove


@bot.callback_query_handler(func=lambda data: re.fullmatch(r"new_order", data.data))
def new_order(data: telebot.types.CallbackQuery):
    # Проверка на регистрацию + определение владельца (нужно для спеццены)
    user_id = data.from_user.id
    owner, employee = get_owner_by_id(user_id)
    if not owner:
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

    if message.text == "Доставить на точку":
        kwargs.update({"pickup": False})

    elif message.text == "Самовывоз":
        kwargs.update({"pickup": True})

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
        if kwargs.get("pickup") is None and kwargs["owner"].pickup:
            send = bot.send_message(message.from_user.id, "Выберите, доставить на точку или самовывоз:",
                                    reply_markup=pickup_markup())
            bot.register_next_step_handler(send, process_new_order_item, **kwargs)
            return

        if kwargs["employee"]:
            if kwargs.get("pickup"):
                order = Order.objects.create(employee=kwargs["employee"], pickup=True)
            else:
                order = Order.objects.create(employee=kwargs["employee"])
        else:
            if kwargs.get("pickup"):
                order = Order.objects.create(owner=kwargs["owner"], pickup=True)
            else:
                order = Order.objects.create(owner=kwargs["owner"])

        order.fill(kwargs["ordered_items"])

        final_message = (f"Ваш заказ принят!\nИтоговая сумма заказа: {order.get_final_info()[1]} руб."
                         f"\n{'Самовывоз' if order.pickup else 'Достака на точку'}"),
        bot.send_message(message.from_user.id, final_message, reply_markup=ReplyKeyboardRemove())
        return

    # Генерируется сообщение для следующего продукта с его ценой и названием
    kwargs["products"] = kwargs["products"][1:]
    next_product = kwargs["products"][0]
    message_text = next_product.generate_message(kwargs["owner"])
    send = bot.send_message(message.from_user.id, message_text, parse_mode="HTML", reply_markup=order_markup())
    kwargs["product_message"] = {"id": send.message_id, "text": send.text}

    bot.register_next_step_handler(send, process_new_order_item, **kwargs)


bot.add_custom_filter(IsOwner())
bot.add_custom_filter(IsRegistered())
