from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("channels/", views.channel_list, name="channel_list"),
    path("channels/new/", views.channel_create, name="channel_create"),
    path("channels/<int:pk>/delete/", views.channel_delete, name="channel_delete"),
    path("themes/<int:theme_pk>/links/", views.channel_link, name="channel_link"),
]
