from .models import Order
from datetime import date


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
