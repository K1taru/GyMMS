from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("", views.payments, name="payments"),
    path("process/", views.process_payment, name="process_payment"),
    path("search-members/", views.search_members, name="search_members"),
    path("transactions/", views.transaction_history, name="transaction_history"),
    path("transactions/stats/", views.transaction_stats, name="transaction_stats"),
]
