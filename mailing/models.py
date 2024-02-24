from django.db import models
from telebot.apihelper import ApiTelegramException

from accounts.models import Owner, Employee
from bot.apps import BotConfig


class Mailing(models.Model):

    text = models.TextField(verbose_name="Текст рассылки")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        owners = list(Owner.objects.filter(has_notifications=True).values_list("tg_id", flat=True))
        employee = list(Employee.objects.filter(has_notifications=True).values_list("tg_id", flat=True))
        users = owners + employee
        for user in users:
            try:
                BotConfig.bot.send_message(user, self.text)
            except ApiTelegramException:
                pass
        self.delete()
