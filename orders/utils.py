import calendar
import datetime
from datetime import date, timedelta
from datetime import datetime as dt

from .models import Order


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


def has_order_today(owner, point=None, pickup=False):
    last_order = Order.objects.filter(
        owner=owner, point=point, pickup=pickup
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


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def create_stats_dict(start: datetime.date, end: datetime.date) -> tuple[tuple, dict]:
    stats_dict = dict()

    for stats_date in daterange(start, end):
        stats_dict[stats_date.isoformat()] = (0, f"{stats_date.day} {calendar.month_name[stats_date.month]} | 0")

    from_month_name = calendar.month_name[start.month]
    to_month_name = calendar.month_name[end.month]
    return (f"{start.day} {from_month_name}", f"{end.day} {to_month_name}"), stats_dict


def get_orders_stats_for_period(orders, start_date=None, end_date=None):

    if start_date and end_date:
        end_date = dt.strptime(end_date, "%Y-%m-%d").date()
        start_date = dt.strptime(start_date, "%Y-%m-%d").date()
    else:
        end_date = dt.now().date()
        start_date = (end_date - timedelta(days=31 * 2)).replace(day=1)

    period, stats = create_stats_dict(start_date, end_date)
    orders = orders.filter(created_at__gte=start_date)

    for order in orders:
        count, price = order.get_final_info()
        year, month, day = order.created_at.year, order.created_at.month, order.created_at.day
        key = order.created_at.strftime("%Y-%m-%d")
        stats[key] = (count,
                      f"{day} {calendar.month_name[month]} | Количество: {count} | Сумма: {price}")

    return stats, period
