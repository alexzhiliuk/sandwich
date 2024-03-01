from django.contrib import admin

from mailing.models import Mailing, Debt


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    pass


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    pass
