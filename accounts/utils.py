import re

from accounts.exceptions import NewUserPhoneNumberError
from accounts.models import Owner, Employee


def get_owner_by_id(tg_id):
    owner = Owner.objects.filter(tg_id=tg_id, is_active=True).first()
    if owner:
        return owner, None

    employee = Employee.objects.filter(tg_id=tg_id, is_active=True, owner__is_active=True).first()
    if employee:
        return employee.owner, employee

    return None, None


def create_phone_number_from_message(message: str):
    numbers = "".join(re.findall(r'\d+', message))[-9:]

    if len(numbers) < 9:
        raise NewUserPhoneNumberError()
    else:
        return f"+375 ({numbers[:2]}) {numbers[2:5]}-{numbers[5:7]}-{numbers[7:]}"
