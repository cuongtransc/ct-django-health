from django.urls import path

from . import views

app_name = 'ct_django_health'

urlpatterns = [path('readyz', views.readyz, name='readyz')]
