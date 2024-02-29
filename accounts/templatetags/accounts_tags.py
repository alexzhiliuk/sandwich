import datetime
from datetime import datetime as dt, timedelta
import calendar

from django import template

register = template.Library()


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


@register.simple_tag
def get_stats_for_point(point, start_date=None, end_date=None):
    orders = point.orders.all()

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
