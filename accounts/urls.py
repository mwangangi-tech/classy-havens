from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/remove-avatar/", views.remove_avatar, name="remove_avatar"), 
    path("password/", views.CustomPasswordChangeView.as_view(), name="password_change"),
]