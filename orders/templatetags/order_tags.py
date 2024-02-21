from django import template

from orders.models import OrderAcceptance
from orders.utils import time_access

register = template.Library()


@register.simple_tag
def access_to_close_acceptance(**kwargs):
    # Вернет True, если время сейчас более 17:05
    return not time_access(17, 5)


@register.simple_tag
def get_order_acceptance(**kwargs):
    return OrderAcceptance.objects.first().get_status_display()
