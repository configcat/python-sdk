from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index1', views.index1, name='index1'),
    path('index2', views.index2, name='index2'),
    path('index3a', views.index3a, name='index3a'),
    path('index3b', views.index3b, name='index3b'),
    path('index4', views.index4, name='index4'),
    path('index5', views.index5, name='index5'),
]
