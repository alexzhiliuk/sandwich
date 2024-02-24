from django.core.management.base import BaseCommand, CommandError
from datetime import datetime as dt

from accounts.models import Owner, Employee

from bot.apps import BotConfig

from telebot.apihelper import ApiTelegramException


class Command(BaseCommand):
    help = "Отрпавить напоминания об оформлении заказа"

    def handle(self, *args, **options):
        owners = list(Owner.objects.filter(has_notifications=True).values_list("tg_id", flat=True))
        employee = list(Employee.objects.filter(has_notifications=True).values_list("tg_id", flat=True))
        users = owners + employee

        weekday = dt.now().weekday()
        if weekday in [0, 1, 2, 3]:
            message = "Добрый день. Заявки сегодня принимаются до 17:00. Не забывайте делать заказ"
        elif weekday == 6:
            message = "Добрый день. Заявки сегодня принимаются до 15:00. Не забывайте делать заказ"
        else:
            raise CommandError('Сегодня не должно быть напоминаний')

        for user in users:
            try:
                BotConfig.bot.send_message(user, message)
            except ApiTelegramException:
                pass

        self.stdout.write(
            self.style.SUCCESS('Напоминания отправлены!')
        )
