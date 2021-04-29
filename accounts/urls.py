from django.contrib import admin
from django.urls import path
from accounts import views
from django.conf.urls import include, url

app_name="accounts"

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
]