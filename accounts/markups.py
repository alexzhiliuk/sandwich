from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def owner_menu_markup():
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Мои точки", callback_data="points"))
    markup.add(InlineKeyboardButton("Мои сотрудники", callback_data="staff"))
    markup.add(InlineKeyboardButton("Новый заказ", callback_data="new_order"))

    return markup


def employee_menu_markup():
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Новый заказ", callback_data="new_order"))

    return markup


def points_markup(points, employee=None):
    markup = InlineKeyboardMarkup()

    for point in points:
        if not employee:
            markup.add(InlineKeyboardButton(point["address"], callback_data=f"point_{point['id']}"))
        else:
            markup.add(
                InlineKeyboardButton(point["address"], callback_data=f"employee_{employee.id}_point_{point['id']}"))

    if not employee:
        markup.add(InlineKeyboardButton("Добавить", callback_data="add_point"))
    else:
        markup.add(InlineKeyboardButton("Открепить от точки", callback_data=f"employee_{employee.id}_point_0"))
        markup.add(InlineKeyboardButton("Назад", callback_data=f"employee_{employee.id}"))

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


def staff_markup(staff):
    markup = InlineKeyboardMarkup()

    for employee in staff:
        markup.add(InlineKeyboardButton(employee["fio"], callback_data=f"employee_{employee['id']}"))

    markup.add(InlineKeyboardButton("Добавить", callback_data="add_employee"))

    return markup


def employee_markup(employee):
    markup = InlineKeyboardMarkup()

    markup.add(InlineKeyboardButton("Изменить точку", callback_data=f"employee_{employee.id}_point"))
    markup.add(InlineKeyboardButton("Удалить", callback_data=f"employee_delete_{employee.id}"))
    markup.add(InlineKeyboardButton("Назад", callback_data=f"back_staff"))

    return markup
