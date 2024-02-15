from accounts.models import Owner, Employee


def get_owner_by_id(tg_id):
    owner = Owner.objects.filter(tg_id=tg_id, is_active=True).first()
    if owner:
        return owner, None

    employee = Employee.objects.filter(tg_id=tg_id, is_active=True).first()
    if employee:
        return employee.owner, employee

    return None
