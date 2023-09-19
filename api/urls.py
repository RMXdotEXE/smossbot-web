from django.urls import path

from . import views


app_name = 'api'

urlpatterns = [
    path('taggedfile/', views.taggedfile, name='taggedfile'),
]