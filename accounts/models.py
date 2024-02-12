from django.db import models


class Owner(models.Model):

    unp = models.CharField(max_length=32, unique=True, db_index=True, verbose_name="УНП")
    fio = models.CharField(max_length=256, unique=True, verbose_name="ФИО")
    tg_id = models.CharField(max_length=64, unique=True, verbose_name="ID в Telegram")
    phone = models.CharField(max_length=32, unique=True, verbose_name="Номер телефона")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    has_notifications = models.BooleanField(default=True, verbose_name="Включить ведомления")
    is_active = models.BooleanField(default=False, verbose_name="Подтвердить регистрацию")

    def __str__(self):
        return f"{self.unp} {self.fio}"

    class Meta:
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"


class Point(models.Model):

    owner = models.ForeignKey(Owner, related_name="points", on_delete=models.PROTECT, verbose_name="Владелец")
    address = models.CharField(max_length=256, unique=True, verbose_name="Адрес")

    def __str__(self):
        return f"{self.address} {self.owner}"

    class Meta:
        verbose_name = "Точка"
        verbose_name_plural = "Точки"


class Employee(models.Model):

    owner = models.ForeignKey(Owner, related_name="staff", on_delete=models.PROTECT, verbose_name="Владелец")
    point = models.ForeignKey(Point, related_name="staff", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Точка")
    fio = models.CharField(max_length=256, unique=True, verbose_name="ФИО")
    tg_id = models.CharField(max_length=64, unique=True, verbose_name="ID в Telegram")
    phone = models.CharField(max_length=32, unique=True, verbose_name="Номер телефона")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    has_notifications = models.BooleanField(default=True, verbose_name="Уведомления")
    is_active = models.BooleanField(default=False, verbose_name="Активный")

    def __str__(self):
        return f"{self.owner.unp} {self.fio}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def set_point(self, point: Point):
        self.point = point
        self.save()

    def unset_point(self):
        self.point = None
        self.save()
