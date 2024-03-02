from django.urls import path

from .views import add_users_from_excel

urlpatterns = [
    path('add-users-from-excel/', add_users_from_excel, name="add-users-from-excel"),
]
