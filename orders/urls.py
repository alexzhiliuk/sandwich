from django.urls import path

from .views import close_acceptance, daily_report

urlpatterns = [
    path('close-acceptance/', close_acceptance, name="close-acceptance"),
    path('daily-report/', daily_report, name="daily-report"),
]
