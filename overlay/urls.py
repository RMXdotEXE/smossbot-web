from django.urls import path

from . import views

app_name = 'overlay'

urlpatterns = [
    path('<user_hash>/', views.process_req, name='process_req'),
]