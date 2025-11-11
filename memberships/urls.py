from django.urls import path
from . import views

app_name = "memberships"

urlpatterns = [
    path("", views.memberships, name="memberships"),
    path("create/", views.create_member, name="create_member"),
    path("member/<str:member_id>/", views.member_detail, name="member_detail"),
    path("member/<str:member_id>/edit/", views.member_detail, name="edit_member"),
    path("member/<str:member_id>/update/", views.update_member, name="update_member"),
    path("member/<str:member_id>/delete/", views.delete_member, name="delete_member"),
]
