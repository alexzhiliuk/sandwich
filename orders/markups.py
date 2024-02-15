from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def order_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3"))
    markup.row(KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6"))
    markup.row(KeyboardButton("Пропустить"))
    markup.row(KeyboardButton("Отмена"))

    return markup


def pickup_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(KeyboardButton("Доставить на точку"))
    markup.row(KeyboardButton("Самовывоз"))

    return markup
