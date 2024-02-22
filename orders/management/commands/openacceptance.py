from django.core.management.base import BaseCommand, CommandError
from orders.models import OrderAcceptance


class Command(BaseCommand):
    help = "Открыть прием заявок"

    def handle(self, *args, **options):
        try:
            acceptance = OrderAcceptance.objects.first()
            acceptance.status = OrderAcceptance.Status.OPEN
            acceptance.save()
        except AttributeError:
            raise CommandError('Объекта статуса приема заявок не существует!')

        self.stdout.write(
            self.style.SUCCESS('Прием заявок открыт!')
        )
