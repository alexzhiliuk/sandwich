from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def owner_menu_markup():
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Мои точки", callback_data="points"))

    return markup


def points_markup(points):

    markup = InlineKeyboardMarkup()

    for point in points:
        markup.add(InlineKeyboardButton(point["address"], callback_data=f"point_{point['id']}"))

    markup.add(InlineKeyboardButton("Добавить", callback_data="add_point"))

    return markup


def point_markup(point):

    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Редактировать", callback_data=f"point_edit_{point.id}"))
    markup.add(InlineKeyboardButton("Удалить", callback_data=f"point_delete_{point.id}"))
    markup.add(InlineKeyboardButton("Назад", callback_data=f"back_points"))

    return markup


def confirm_markup(confirm_btn, back_btn):
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton(confirm_btn["text"], callback_data=confirm_btn["callback"]))
    markup.add(InlineKeyboardButton(back_btn["text"], callback_data=back_btn["callback"]))

    return markup
