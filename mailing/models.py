from django.core.exceptions import ValidationError
from django.db import models
from telebot.apihelper import ApiTelegramException

from accounts.models import Owner, Employee
from django.conf import settings
from bot.apps import BotConfig

from .excel import ExcelDebtsMailing


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


class Debt(models.Model):

    file = models.FileField(upload_to="debts/", verbose_name="Файл Excel")
    mailing_now = models.BooleanField(default=False, verbose_name="Сделать рассылку сейчас")

    def clean(self, *args, **kwargs):
        super().clean()
        if self.file.url.split(".")[-1] != "xlsx":
            raise ValidationError('Неподдерживоемое расширение файла. Используйте .xlsx')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.mailing_now:
            debts = ExcelDebtsMailing(settings.BASE_DIR / self.file.path)
            debts.mailing()
            self.delete()

    def __str__(self):
        return "Файл с задолженностями"

    class Meta:
        verbose_name = "Долги"
        verbose_name_plural = "Долги"

