"""Capa HTTP de vendedores UISEK: valida formato -> invoca services/selectors -> serializa."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import services as account_services
from apps.accounts.models import OTPPurpose
from apps.accounts.serializers import (
    OTPCodeSerializer,
    OTPRequestResponseSerializer,
    UserMeSerializer,
)
from apps.core.serializers import ErrorResponseSerializer
from apps.core.throttling import ClientIPRateThrottle
from apps.sellers import selectors, services
from apps.sellers.permissions import IsActiveSeller
from apps.sellers.serializers import (
    SellerApplicationCreateSerializer,
    SellerApplicationSerializer,
    SellerOwnProfileSerializer,
    SellerProfileUpdateSerializer,
    SellerPublicProfileSerializer,
    UisekOTPRequestSerializer,
)

TAG = ["sellers"]
ERR = ErrorResponseSerializer


class UisekOTPRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "otp_request"

    @extend_schema(
        operation_id="sellers_uisek_otp_request",
        tags=TAG,
        request=UisekOTPRequestSerializer,
        summary="Envía un OTP al correo institucional @uisek.edu.ec (UISEK_SELLER).",
        responses={200: OTPRequestResponseSerializer, 400: ERR, 403: ERR, 409: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = UisekOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = account_services.request_email_otp(
            request.user, OTPPurpose.UISEK_SELLER, serializer.validated_data["uisek_email"]
        )
        return Response(OTPRequestResponseSerializer(otp).data)


class UisekOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ClientIPRateThrottle]
    throttle_scope = "otp_verify"

    @extend_schema(
        operation_id="sellers_uisek_otp_verify",
        tags=TAG,
        request=OTPCodeSerializer,
        summary="Verifica el OTP UISEK_SELLER y vincula el correo institucional.",
        responses={200: UserMeSerializer, 400: ERR, 403: ERR, 409: ERR, 429: ERR},
    )
    def post(self, request):
        serializer = OTPCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = account_services.verify_email_otp(
            request.user, OTPPurpose.UISEK_SELLER, serializer.validated_data["code"]
        )
        return Response(UserMeSerializer(user).data)


class SellerApplicationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="sellers_applications_create",
        tags=TAG,
        request=SellerApplicationCreateSerializer,
        responses={201: SellerApplicationSerializer, 400: ERR, 403: ERR, 409: ERR},
    )
    def post(self, request):
        serializer = SellerApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = services.submit_seller_application(request.user, **serializer.validated_data)
        return Response(
            SellerApplicationSerializer(application).data, status=status.HTTP_201_CREATED
        )


class MySellerApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="sellers_applications_me",
        tags=TAG,
        summary="Solicitudes del usuario, de la más reciente a la más antigua.",
        description=(
            "Devuelve todas las solicitudes ordenadas por -created_at. El primer elemento es la "
            "solicitud vigente; lista vacía si el usuario nunca postuló."
        ),
        responses={200: SellerApplicationSerializer(many=True), 403: ERR},
    )
    def get(self, request):
        applications = selectors.list_user_applications(request.user)
        return Response(SellerApplicationSerializer(applications, many=True).data)


class SellerPublicProfileView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="sellers_profile_retrieve",
        tags=TAG,
        responses={
            200: SellerPublicProfileSerializer,
            404: OpenApiResponse(ERR, description="NOT_FOUND: no existe o no está activo."),
        },
    )
    def get(self, request, id):  # "id": nombre del contrato /sellers/{id}/
        profile = selectors.get_public_seller_profile(id)
        if profile is None:
            raise NotFound()
        return Response(SellerPublicProfileSerializer(profile).data)


class SellerMeView(APIView):
    permission_classes = [IsAuthenticated, IsActiveSeller]

    @extend_schema(
        operation_id="sellers_me_retrieve",
        tags=TAG,
        summary="Perfil completo del vendedor autenticado (incluye contact_phone).",
        responses={200: SellerOwnProfileSerializer, 403: ERR},
    )
    def get(self, request):
        # Solo lectura: IsActiveSeller ya garantizó que existe un perfil activo.
        profile = selectors.get_active_seller_profile_for_user(request.user)
        return Response(SellerOwnProfileSerializer(profile).data)

    @extend_schema(
        operation_id="sellers_me_update",
        tags=TAG,
        request=SellerProfileUpdateSerializer,
        responses={200: SellerOwnProfileSerializer, 400: ERR, 403: ERR},
    )
    def patch(self, request):
        serializer = SellerProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = services.update_seller_profile(request.user, **serializer.validated_data)
        return Response(SellerOwnProfileSerializer(profile).data)
