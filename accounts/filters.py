import telebot

from accounts.models import Owner, Employee


class IsRegistered(telebot.custom_filters.SimpleCustomFilter):
    key = 'is_registered'

    @staticmethod
    def check(message: telebot.types.Message):
        return Owner.objects.filter(tg_id=message.from_user.id, is_active=True).exists() or Employee.objects.filter(
            tg_id=message.from_user.id, is_active=True).exists()


class IsOwner(telebot.custom_filters.SimpleCustomFilter):
    key = 'is_owner'

    @staticmethod
    def check(message: telebot.types.Message):
        return Owner.objects.filter(tg_id=message.from_user.id, is_active=True).exists()
