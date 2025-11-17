from django.urls import path
from . import views

app_name = "metrics"

urlpatterns = [
    path("", views.metrics, name="metrics"),
    path("api/data/", views.get_metrics_data, name="get_metrics_data"),
]
