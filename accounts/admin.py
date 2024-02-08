from django.contrib import admin
from .models import *


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at"]
    search_fields = ["unp", "fio", "phone"]
    fieldsets = [
        (
            "Персональная информация",
            {
                "fields": ["unp", "fio", "username", "phone"],
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
    ]


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    search_fields = ["owner", "address"]
    autocomplete_fields = ["owner"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at"]
    search_fields = ["owner", "fio", "phone"]
    autocomplete_fields = ["owner", "point"]
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
                "fields": ["fio", "username", "phone"],
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
    ]

