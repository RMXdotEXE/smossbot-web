from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

app_name = 'functions'

urlpatterns = [
    path('', views.index, name='index'),
    path('reward/', views.reward, name='reward'),
    path('configure/', views.configure, name='configure'),
    path('binds/', views.binds, name='binds'),
    path('vars/', views.vars, name='vars'),
]

urlpatterns = format_suffix_patterns(urlpatterns)