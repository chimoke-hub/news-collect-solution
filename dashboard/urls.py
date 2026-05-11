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
    path("themes/<int:pk>/reset/", views.theme_reset, name="theme_reset"),
    path("themes/<int:pk>/collect/", views.collect_now, name="collect_now"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),
    path("articles/<int:pk>/favorite/", views.article_favorite_toggle, name="article_favorite"),
    path("favorites/", views.favorites, name="favorites"),
]
