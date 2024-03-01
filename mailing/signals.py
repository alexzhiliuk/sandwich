from django.dispatch import receiver
from django.db.models.signals import pre_delete
from .models import Debt


@receiver(pre_delete, sender=Debt)
def debt_delete(sender, instance, **kwargs):
    instance.file.delete(False)
