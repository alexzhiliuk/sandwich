from django.contrib import admin

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


# fieldsets = [
#         (
#             "Персональная информация",
#             {
#                 "fields": ["unp", "fio", "phone", "tg_id"],
#             },
#         ),
#         (
#             "Уведомления",
#             {
#                 "fields": ["has_notifications"],
#             },
#         ),
#         (
#             "Важные даты",
#             {
#                 "fields": ["created_at"],
#             },
#         ),
#         (
#             "Доступ",
#             {
#                 "fields": ["is_active"],
#             },
#         ),
#     ]
