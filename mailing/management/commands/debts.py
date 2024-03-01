from django.core.management.base import BaseCommand, CommandError

from mailing.excel import ExcelDebtsMailing
from django.conf import settings

from mailing.models import Debt


class Command(BaseCommand):
    help = "Отрпавить напоминания о задолженности"

    def handle(self, *args, **options):

        debt = Debt.objects.last()
        debts = ExcelDebtsMailing(settings.BASE_DIR / debt.file.path)
        debts.mailing()
        debt.delete()

        self.stdout.write(
            self.style.SUCCESS('Напоминания о задолженности отправлены!')
        )
