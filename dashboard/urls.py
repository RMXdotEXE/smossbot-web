from django.urls import path, include, re_path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('bind/', views.bind, name='bind'),
    path('unbind/', views.unbind, name='unbind'),
    path('create/', views.create, name='create'),
    path('callAPI/', views.callAPI, name='callAPI'),
    path('delete/', views.delete, name='delete'),
    path('upload/', views.upload, name='upload'),
    path('upload/changeTag/', views.changeTag, name='changeTag'),
    path('upload/deleteFile', views.deleteFile, name='deleteFile'),
    path('deleteFiles/', views.deleteFiles, name='deleteFiles')
]