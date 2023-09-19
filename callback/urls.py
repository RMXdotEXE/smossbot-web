from django.urls import path

from . import views

app_name = 'callback'

urlpatterns = [
    path('twitch/', views.twitch, name='twitch'),
    path('spotify/', views.spotify, name='spotify'),
]