import datetime
from datetime import datetime as dt, timedelta
import calendar

from django import template

from orders.utils import get_orders_stats_for_period

register = template.Library()


@register.simple_tag
def get_stats_for_point(point, start_date=None, end_date=None):
    if not point:
        return
    orders = point.orders.all()
    return get_orders_stats_for_period(orders, start_date, end_date)


@register.simple_tag
def get_stats_for_owner(owner, start_date=None, end_date=None):
    if not owner:
        return
    orders = owner.orders.all()
    return get_orders_stats_for_period(orders, start_date, end_date)
