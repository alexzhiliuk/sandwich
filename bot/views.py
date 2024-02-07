from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import telebot

WEBHOOK = "8fo2jlap55.loclx.io"

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.remove_webhook()
bot.set_webhook(WEBHOOK)
# https://api.telegram.org/bot6734680296:AAGIYNPcYGlVBKI0tMq8__6SFshRfW2O9_w/setWebhook?url=https://13ac-151-249-178-223.ngrok-free.app/


@csrf_exempt
def index(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

    return HttpResponse("OK")


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    name = ''
    if message.from_user.last_name is None:
        name = f'{message.from_user.first_name}'
    else:
        name = f'{message.from_user.first_name} {message.from_user.last_name}'
    bot.send_message(message.chat.id, f'Привет! {name}\n'
                                      f'Я бот, который будет спамить вам беседу :)\n\n'
                                      f'Чтобы узнать больше команд, напишите /help')
