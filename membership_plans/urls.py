from django.urls import path
from . import views

app_name = "membership_plans"

urlpatterns = [
    path("", views.base, name="base"),
]
