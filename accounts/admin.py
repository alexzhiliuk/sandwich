from django.contrib import admin
from .models import *


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "tg_id"]
    search_fields = ["unp", "fio", "phone"]
    list_filter = ["is_active"]
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
                "fields": ["is_active"],
            },
        ),
    ]


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    search_fields = ["owner", "address"]
    autocomplete_fields = ["owner"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "tg_id"]
    search_fields = ["owner", "fio", "phone"]
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
