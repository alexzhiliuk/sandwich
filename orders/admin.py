from django.contrib import admin
from django.utils.html import format_html

from .models import *


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_filter = ["product_type"]
    autocomplete_fields = ["product_type"]
    list_display = ["name", "price", "product_type"]


@admin.register(SpecialPrice)
class SpecialPriceAdmin(admin.ModelAdmin):
    search_fields = ["owner", "product"]
    list_filter = ["owner", "product"]
    autocomplete_fields = ["owner", "product"]
    list_display = ["product", "price", "owner"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["price"]

    @admin.display(description='Цена')
    def price(self, obj):
        html = '<span>{price} руб.</span>'
        return format_html(''.join(html.format(price=obj.price)))


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_filter = ["pickup"]
    list_display = ["owner", "employee", "created_at"]
    inlines = [OrderItemInline]
    readonly_fields = ["created_at", "result"]
    list_display_links = ["owner", "employee"]

    @admin.display(description='Итог')
    def result(self, obj):
        count, price = obj.get_final_info()
        html = '<span>Цена: {price} руб.</span><br><span>Количество: {count}</span>'
        return format_html(''.join(html.format(price=price, count=count)))

    fieldsets = [
        (
            "Кто заказал",
            {
                "fields": ["owner", "employee"],
            },
        ),
        (
            "Информация",
            {
                "fields": ["pickup", "created_at", "result"],
            },
        )
    ]
