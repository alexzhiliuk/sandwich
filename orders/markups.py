from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .models import Product


def order_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(KeyboardButton("Пропустить"))
    markup.row(KeyboardButton("Отмена"))

    return markup


def pickup_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(KeyboardButton("Доставить на точку"))
    markup.row(KeyboardButton("Самовывоз"))

    return markup


def order_points_markup(points):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    for point in points:
        markup.row(KeyboardButton(point.address))

    markup.row(KeyboardButton("Отмена"))

    return markup


def orders_markup(orders):
    markup = InlineKeyboardMarkup()

    for index, order in enumerate(orders):
        btn_text = f"{index + 1}: {order['created_at'].date().strftime('%Y-%m-%d')}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"update_order_{order['id']}"))

    return markup


def order_products_markup(order_id, page=1):
    markup = InlineKeyboardMarkup()

    products = Product.objects.all().values("id", "name")
    pages = len(products) // (5 + 1) + 1

    start_index = (page - 1) * 5
    end_index = page * 5
    products = products[start_index:end_index]

    for product in products:
        btn_text = f"{product['name']}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"update_order_{order_id}_product_{product['id']}"))

    if page != 1:
        markup.add(InlineKeyboardButton("<<<", callback_data=f"update_order_{order_id}_page_{page - 1}"))
    if page != pages:
        markup.add(InlineKeyboardButton(">>>", callback_data=f"update_order_{order_id}_page_{page + 1}"))

    markup.add(InlineKeyboardButton("Готово", callback_data=f"update_order"))

    return markup


def order_products_count_markup(order_id, product_id):
    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("1", callback_data=f"update_order_{order_id}_product_{product_id}_count_1"),
        InlineKeyboardButton("2", callback_data=f"update_order_{order_id}_product_{product_id}_count_2"),
        InlineKeyboardButton("3", callback_data=f"update_order_{order_id}_product_{product_id}_count_3"),
    )
    markup.row(
        InlineKeyboardButton("4", callback_data=f"update_order_{order_id}_product_{product_id}_count_4"),
        InlineKeyboardButton("5", callback_data=f"update_order_{order_id}_product_{product_id}_count_5"),
        InlineKeyboardButton("6", callback_data=f"update_order_{order_id}_product_{product_id}_count_6"),
    )
    markup.add(
        InlineKeyboardButton("Другое кол-во",
                             callback_data=f"update_order_{order_id}_product_{product_id}_count")
    )
    markup.add(
        InlineKeyboardButton("Удалить",
                             callback_data=f"update_order_{order_id}_product_{product_id}_delete")
    )

    markup.add(InlineKeyboardButton("Отмена", callback_data=f"update_order_{order_id}"))

    return markup
