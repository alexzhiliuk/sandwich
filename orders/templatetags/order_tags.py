from datetime import datetime as dt

from django import template

from orders.models import OrderAcceptance, OrderItem
from orders.utils import time_access

register = template.Library()


@register.simple_tag
def access_to_close_acceptance(**kwargs):
    # Вернет True, если время сейчас более 17:05 для пн-чт и более 15:05 для вс
    weekday = dt.now().weekday()
    if weekday in [0, 1, 2, 3]:
        return not time_access(17, 5)
    if weekday == 6:
        return not time_access(15, 5)
    # Если это пятница или суббота, то закрыть прием заявок нельзя
    return False


@register.simple_tag
def get_order_acceptance(**kwargs):
    return OrderAcceptance.objects.first().get_status_display()


@register.simple_tag
def get_created_orders_stats():
    return OrderItem.get_stats()
