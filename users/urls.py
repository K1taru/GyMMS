from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("", views.base, name="base"),
    path("admin/", views.admin_panel, name="admin"),
    path("admin/staff/create/", views.create_staff, name="create_staff"),
    path("admin/staff/<int:staff_id>/", views.get_staff, name="get_staff"),
    path("admin/staff/update/", views.update_staff, name="update_staff"),
    path("admin/staff/delete/<int:staff_id>/", views.delete_staff, name="delete_staff"),
    path("admin/pricing/create/", views.create_pricing, name="create_pricing"),
    path("admin/pricing/<int:pricing_id>/", views.get_pricing, name="get_pricing"),
    path("admin/pricing/update/", views.update_pricing, name="update_pricing"),
    path("admin/pricing/delete/<int:pricing_id>/", views.delete_pricing, name="delete_pricing"),
]
