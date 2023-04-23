from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('twitch/', views.twitch, name='twitch'),
    path('spotify/', views.spotify, name='spotify'),
    path('send_data/', views.send_data, name='send_data'),
    path('after_auth/', views.after_auth, name='after_auth'),
    path('bind/', views.bind, name='bind'),
]