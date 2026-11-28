from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.CsrfCookieView.as_view(), name="csrf"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/delete/", views.AccountDeleteView.as_view(), name="me-delete"),
    path("email-otp/request/", views.EmailOTPRequestView.as_view(), name="email-otp-request"),
    path("email-otp/verify/", views.EmailOTPVerifyView.as_view(), name="email-otp-verify"),
    path(
        "password-reset/request/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password-change/", views.PasswordChangeView.as_view(), name="password-change"),
]
