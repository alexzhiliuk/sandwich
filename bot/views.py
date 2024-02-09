from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import telebot

WEBHOOK = "dn0w9qpplo.loclx.io"

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.remove_webhook()
bot.set_webhook(WEBHOOK)

from accounts.views import *


@csrf_exempt
def index(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

    return HttpResponse("OK")


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):

    bot.send_message(message.chat.id, 'Стартовое сообщение. Команды: \n/reg\n/menu')
