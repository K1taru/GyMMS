from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("qrph/attempts/", views.qrph_create, name="qrph_create"),
    path("qrph/current/", views.qrph_current, name="qrph_current"),
    path("qrph/attempts/<uuid:attempt_id>/", views.qrph_detail, name="qrph_detail"),
    path("qrph/attempts/<uuid:attempt_id>/cancel/", views.qrph_cancel, name="qrph_cancel"),
    path("webhooks/paymongo/<str:mode>/", views.paymongo_webhook, name="paymongo_webhook"),
    path("", views.payments, name="payments"),
    path("process/", views.process_payment, name="process_payment"),
    path("search-members/", views.search_members, name="search_members"),
    path("transactions/", views.transaction_history, name="transaction_history"),
    path("transactions/stats/", views.transaction_stats, name="transaction_stats"),
    path("transactions/ajax/", views.get_transactions_ajax, name="get_transactions_ajax"),
]
