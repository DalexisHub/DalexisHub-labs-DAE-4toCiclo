from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('api-test/', views.api_test, name='api_test'),
    path('api/items/', views.item_api_list, name='item_api_list'),
]