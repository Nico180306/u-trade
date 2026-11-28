from django.urls import path

from apps.sellers import views

app_name = "sellers"

urlpatterns = [
    path("uisek-otp/request/", views.UisekOTPRequestView.as_view(), name="uisek-otp-request"),
    path("uisek-otp/verify/", views.UisekOTPVerifyView.as_view(), name="uisek-otp-verify"),
    path("applications/", views.SellerApplicationCreateView.as_view(), name="applications"),
    path("applications/me/", views.MySellerApplicationsView.as_view(), name="applications-me"),
    path("me/", views.SellerMeView.as_view(), name="me"),
    path("<uuid:id>/", views.SellerPublicProfileView.as_view(), name="profile"),
]
