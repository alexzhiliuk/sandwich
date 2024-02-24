from django.contrib import admin
from .models import *
from orders.admin import SpecialPriceInline


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "tg_id"]
    search_fields = ["unp", "fio", "phone"]
    list_filter = ["is_active"]
    inlines = [SpecialPriceInline]
    fieldsets = [
        (
            "Персональная информация",
            {
                "fields": ["unp", "fio", "phone", "tg_id"],
            },
        ),
        (
            "Уведомления",
            {
                "fields": ["has_notifications"],
            },
        ),
        (
            "Важные даты",
            {
                "fields": ["created_at"],
            },
        ),
        (
            "Доступ",
            {
                "fields": ["pickup", "is_active"],
            },
        ),
    ]


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    search_fields = ["owner__unp", "owner__fio", "address"]
    autocomplete_fields = ["owner"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "tg_id"]
    search_fields = ["owner__unp", "owner__fio", "fio", "phone"]
    autocomplete_fields = ["owner", "point"]
    list_filter = ["is_active"]
    fieldsets = [
        (
            "Владелец/точка",
            {
                "fields": ["owner", "point"],
            },
        ),
        (
            "Персональная информация",
            {
                "fields": ["fio", "phone", "tg_id"],
            },
        ),
        (
            "Уведомления",
            {
                "fields": ["has_notifications"],
            },
        ),
        (
            "Важные даты",
            {
                "fields": ["created_at"],
            },
        ),
        (
            "Доступ",
            {
                "fields": ["is_active"],
            },
        ),
    ]
