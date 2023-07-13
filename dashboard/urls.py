from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('twitch/', views.twitch, name='twitch'),
    path('spotify/', views.spotify, name='spotify'),
    path('bind/', views.bind, name='bind'),
    path('unbind/', views.unbind, name='unbind'),
    path('create/', views.create, name='create'),
    path('callAPI/', views.callAPI, name='callAPI'),
    path('delete/', views.delete, name='delete')
]