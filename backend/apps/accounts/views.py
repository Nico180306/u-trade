"""Capa HTTP de Auth Core: valida formato -> invoca services/selectors -> serializa.

Las vistas POST anónimas usan csrf_protect porque SessionAuthentication de DRF solo aplica CSRF
a usuarios autenticados.
"""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.models import OTPPurpose
from apps.accounts.serializers import (
    AccountDeleteSerializer,
    LoginSerializer,
    OTPCodeSerializer,
    OTPRequestResponseSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserMeSerializer,
)
from apps.core.serializers import ErrorResponseSerializer
from apps.core.throttling import ClientIPRateThrottle

TAG = ["auth"]
ERR = ErrorResponseSerializer
NO_CONTENT = OpenApiResponse(description="Sin contenido.")


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfCookieView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="auth_csrf",
        tags=TAG,
        responses={204: OpenApiResponse(description="Emite la cookie csrftoken.")},
    )
    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "register"

    @extend_schema(
        operation_id="auth_register",
        tags=TAG,
        request=RegisterSerializer,
        responses={201: UserMeSerializer, 400: ERR, 403: ERR, 409: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(**serializer.validated_data)
        services.start_session(request, user)
        return Response(UserMeSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        operation_id="auth_login",
        tags=TAG,
        request=LoginSerializer,
        responses={200: UserMeSerializer, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.login_user(request, **serializer.validated_data)
        return Response(UserMeSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="auth_logout", tags=TAG, request=None, responses={204: NO_CONTENT, 403: ERR}
    )
    def post(self, request):
        services.end_session(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="auth_me_retrieve",
        tags=TAG,
        responses={
            200: UserMeSerializer,
            403: OpenApiResponse(ERR, description="NOT_AUTHENTICATED: no hay sesión activa."),
        },
    )
    def get(self, request):
        return Response(UserMeSerializer(request.user).data)

    @extend_schema(
        operation_id="auth_me_update",
        tags=TAG,
        request=ProfileUpdateSerializer,
        responses={200: UserMeSerializer, 400: ERR, 403: ERR},
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = services.update_profile(request.user, **serializer.validated_data)
        return Response(UserMeSerializer(user).data)


class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        operation_id="auth_me_delete",
        tags=TAG,
        request=AccountDeleteSerializer,
        responses={204: NO_CONTENT, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = AccountDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        services.verify_current_password(user, serializer.validated_data["current_password"])
        services.anonymize_user_account(user)
        services.end_session(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "password_reset"

    @extend_schema(
        operation_id="auth_password_reset_request",
        tags=TAG,
        request=PasswordResetRequestSerializer,
        responses={204: NO_CONTENT, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(**serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "password_reset"

    @extend_schema(
        operation_id="auth_password_reset_confirm",
        tags=TAG,
        request=PasswordResetConfirmSerializer,
        responses={204: NO_CONTENT, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(**serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "auth"

    @extend_schema(
        operation_id="auth_password_change",
        tags=TAG,
        request=PasswordChangeSerializer,
        responses={204: NO_CONTENT, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(request, request.user, **serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Verificación OTP del correo de comprador (purpose = BUYER_EMAIL) ----------------------


class EmailOTPRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "otp_request"

    @extend_schema(
        operation_id="auth_email_otp_request",
        tags=TAG,
        request=None,
        summary="Envía un OTP de 6 dígitos al correo de registro (BUYER_EMAIL).",
        responses={200: OTPRequestResponseSerializer, 400: ERR, 403: ERR, 429: ERR},
    )
    def post(self, request):
        otp = services.request_email_otp(request.user, OTPPurpose.BUYER_EMAIL)
        return Response(OTPRequestResponseSerializer(otp).data)


class EmailOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "otp_verify"

    @extend_schema(
        operation_id="auth_email_otp_verify",
        tags=TAG,
        request=OTPCodeSerializer,
        summary="Verifica el OTP BUYER_EMAIL (atajo: @uisek.edu.ec verifica también UISEK).",
        responses={200: UserMeSerializer, 400: ERR, 403: ERR, 409: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = OTPCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.verify_email_otp(
            request.user, OTPPurpose.BUYER_EMAIL, serializer.validated_data["code"]
        )
        return Response(UserMeSerializer(user).data)
