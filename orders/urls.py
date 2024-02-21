from django.urls import path

from .views import close_acceptance

urlpatterns = [
    path('close-acceptance/', close_acceptance, name="close-acceptance"),
]
