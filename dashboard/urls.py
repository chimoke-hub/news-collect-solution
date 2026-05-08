from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("themes/", views.theme_list, name="theme_list"),
    path("themes/new/", views.theme_create, name="theme_create"),
    path("themes/<int:pk>/", views.theme_detail, name="theme_detail"),
    path("themes/<int:pk>/edit/", views.theme_edit, name="theme_edit"),
    path("themes/<int:pk>/delete/", views.theme_delete, name="theme_delete"),
    path("themes/<int:pk>/collect/", views.collect_now, name="collect_now"),
]
