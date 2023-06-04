from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('twitch/', views.twitch, name='twitch'),
    path('spotify/', views.spotify, name='spotify'),
    path('bind/', views.bind, name='bind'),
    path('callAPI/', views.callAPI, name='callAPI'),
    path('resend/', views.resend, name='resend')
]