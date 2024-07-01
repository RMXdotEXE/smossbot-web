from django.urls import path

from . import views


app_name = 'overlay'

urlpatterns = [
    path('user/<str:user_hash>/', views.process_req, name='process_req'),
    path('configure/', views.configure, name='configure'),
    path('configurations/', views.configurations, name='configurations')
]