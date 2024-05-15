from django.urls import path

from . import views


app_name = 'api'

urlpatterns = [
    path('session/', views.session, name='session'),
    path('taggedfile/', views.taggedfile, name='taggedfile'),
]