from .models import Order
from datetime import date, timedelta
from datetime import datetime as dt


def get_weekends_dates():
    today = date.today()
    dates = [today]
    if today.weekday() == 4:
        dates.append(today + timedelta(1))
        dates.append(today + timedelta(2))
    elif today.weekday() == 5:
        dates.append(today + timedelta(1))
        dates.append(today - timedelta(1))
    else:
        dates.append(today - timedelta(1))
        dates.append(today - timedelta(2))

    return dates


def has_order_today(employee=None, owner=None, point=None, pickup=False):
    if employee:
        last_order = Order.objects.filter(employee=employee).order_by("-created_at").first()
        if not last_order:
            return False

        weekday = date.today().weekday()
        if weekday in [0, 1, 2, 3]:
            if date.today() == last_order.created_at.date():
                return True
        else:
            dates = get_weekends_dates()
            if last_order.created_at.date() in dates:
                return True

        return False

    if owner:
        last_order = Order.objects.filter(
            owner=owner, employee=None, point=point, pickup=pickup
        ).order_by("-created_at").first()
        if not last_order:
            return False

        weekday = date.today().weekday()
        if weekday in [0, 1, 2, 3]:
            if date.today() == last_order.created_at.date():
                return True
        else:
            dates = get_weekends_dates()
            if last_order.created_at.date() in dates:
                return True

        return False


def time_access(hour, minute):
    now = dt.now().time()
    return True if now.hour < hour or (now.hour == hour and now.minute <= minute) else False

