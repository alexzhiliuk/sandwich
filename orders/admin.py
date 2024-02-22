from django.contrib import admin, messages
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
    search_fields = ["owner__unp", "owner__fio", "product__name"]
    list_filter = ["owner", "product"]
    autocomplete_fields = ["owner", "product"]
    list_display = ["product", "price", "owner"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["price"]

    @admin.display(description='Цена')
    def price(self, obj):
        price = obj.price
        html = '<span><b>{price} руб.</b><br>({piece} руб. за шт.)</span>'
        return format_html(''.join(html.format(price=price, piece=round(price / obj.count, 2))))


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_filter = ["pickup", "status"]
    list_display = ["owner", "employee", "created_at", "delivery", "status"]
    autocomplete_fields = ["owner", "point"]
    inlines = [OrderItemInline]
    readonly_fields = ["created_at", "result"]
    list_display_links = ["owner", "employee"]
    change_list_template = "admin/custom_order_admin.html"

    @admin.display(description='Итог')
    def result(self, obj):
        count, price = obj.get_final_info()
        html = '<span>Цена: {price} руб.</span><br><span>Количество: {count}</span>'
        return format_html(''.join(html.format(price=price, count=count)))

    @admin.display(description='Доставка')
    def delivery(self, obj):
        if obj.pickup:
            point = "Самовывоз"
        else:
            try:
                point = obj.point.address
            except AttributeError:
                point = "Не указано (точка была удалена)"

        html = '<span>{point}</span>'
        return format_html(''.join(html.format(point=point)))

    fieldsets = [
        (
            "Статус",
            {
                "fields": ["status"],
            },
        ),
        (
            "Кто заказал",
            {
                "fields": ["owner", "employee"],
            },
        ),
        (
            "Информация",
            {
                "fields": ["point", "pickup", "created_at", "result"],
            },
        )
    ]


@admin.register(OrderAcceptance)
class OrderAcceptanceAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        count = OrderAcceptance.objects.count()
        if count == 0 or count == 1 and change:
            return super().save_model(request, obj, form, change)
        messages.add_message(request, messages.ERROR, 'Объект статуса приема заказов может быть только 1!')

    def delete_model(self, request, obj):
        if OrderAcceptance.objects.count() == 1:
            messages.add_message(request, messages.ERROR, 'Объект статуса приема нельзя удалить!')
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        messages.add_message(request, messages.ERROR, 'Объект статуса приема нельзя удалить!')
        return

