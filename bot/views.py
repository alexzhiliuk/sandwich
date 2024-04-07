from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bot.apps import BotConfig

from accounts.views import *
from orders.views import *

bot = BotConfig.bot


@csrf_exempt
def index(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

    return HttpResponse("OK")


@bot.message_handler(commands=['start', 'help'])
def start(message: telebot.types.Message):
    parameter = message.text.split(" ")[-1]
    if parameter.isnumeric():

        user_id = message.from_user.id
        if Owner.objects.filter(tg_id=user_id).exists() or Employee.objects.filter(tg_id=user_id).exists():
            bot.send_message(user_id, 'Вы уже зарегистрированы в системе!')
            return

        owner = Owner.objects.filter(tg_id=parameter).first()
        if not owner:
            bot.send_message(message.from_user.id,
                             "С регистрационной ссылкой что-то не так. Обратитесь к администратору")
            return

        send = bot.send_message(message.from_user.id, "Введите ваш номер телефона:")
        bot.register_next_step_handler(send, process_employee_phone, owner)
        return

    bot.send_message(
        message.chat.id,
        'Добро пожаловать! Если Вы уже зарегистрированы, то можете воспользовататься следующими коммандами: \n\n'
        '/new_order - Создать новый заказ\n'
        '/edit_order - Редактировать заказ\n'
        '/menu - Главное меню, в котором Вы можете управлять своими точками и сотрудниками (Только для владельцев)\n\n'
        'Если Вы еще не зарегистрированы в боте, то воспользуйтесь командой /reg'
    )


@bot.message_handler(commands=['menu'])
def menu(message: telebot.types.Message):
    user_id = message.from_user.id

    if Owner.objects.filter(tg_id=user_id).exists():
        bot.send_message(user_id, 'Меню:', reply_markup=owner_menu_markup())
    elif Employee.objects.filter(tg_id=user_id).exists():
        bot.send_message(user_id, "Для вас данная функция недоступна, воспользуйтесь командами: "
                                  "\n\n/new_order - Создать новый заказ\n/edit_order - Редактировать заказ")
    else:
        bot.send_message(user_id, "Вы не зарегистрированы либо администратор еще не подтвердил вашу регистрацию!")
