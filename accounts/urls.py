from django.contrib import admin
from django.urls import path
from accounts import views
from django.conf.urls import include, url

app_name="accounts"

#  url path and and definition of the view to be used
urlpatterns = [
    path('login/', views.user_login, name='user_login'),
]