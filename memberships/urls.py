from django.urls import path
from . import views

app_name = "memberships"

urlpatterns = [
    path("", views.base, name="base"),
]
