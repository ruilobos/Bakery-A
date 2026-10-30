from django.urls import path

from accounts import views

app_name = "accounts"

#  url path and and definition of the view to be used
urlpatterns = [
    path("login/", views.user_login, name="user_login"),
]
