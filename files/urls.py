from django.urls import path

from . import views

app_name = 'files'

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.files, name='files'),
]