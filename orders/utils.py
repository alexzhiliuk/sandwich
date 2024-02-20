from .models import Order
from datetime import date
from datetime import datetime as dt


def has_order_today(employee=None, owner=None, point=None, pickup=False):
    if employee:
        last_order = Order.objects.filter(employee=employee).order_by("-created_at").first()
        if not last_order:
            return False
        if date.today() == last_order.created_at.date():
           return True
        return False

    if owner:
        last_order = Order.objects.filter(owner=owner, point=point, pickup=pickup).order_by("-created_at").first()
        if not last_order:
            return False
        if date.today() == last_order.created_at.date():
           return True
        return False


def time_access(hour, minute):
    now = dt.now().time()
    return True if now.hour < hour or (now.hour == hour and now.minute <= minute) else False

