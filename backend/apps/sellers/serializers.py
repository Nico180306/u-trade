"""Validación de formato y serialización de vendedores. Sin reglas de negocio."""

from rest_framework import serializers

from apps.sellers.models import SellerApplication, SellerProfile

PHONE_REGEX = r"^\+?[0-9][0-9 \-]{6,18}$"
INSTAGRAM_REGEX = r"^@?[A-Za-z0-9._]{1,30}$"


def _phone_field(**kwargs) -> serializers.RegexField:
    return serializers.RegexField(
        PHONE_REGEX,
        max_length=20,
        error_messages={"invalid": "Ingresa un teléfono válido (solo dígitos, espacios o +)."},
        **kwargs,
    )


class UisekOTPRequestSerializer(serializers.Serializer):
    uisek_email = serializers.EmailField(max_length=254)


class SellerApplicationCreateSerializer(serializers.Serializer):
    venture_name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=1000)
    contact_phone = _phone_field()
    instagram_handle = serializers.RegexField(
        INSTAGRAM_REGEX,
        max_length=31,
        required=False,
        allow_blank=True,
        default="",
        error_messages={"invalid": "Usuario de Instagram no válido."},
    )

    def validate_instagram_handle(self, value: str) -> str:
        return value.lstrip("@")


class SellerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerApplication
        fields = [
            "id",
            "venture_name",
            "description",
            "contact_phone",
            "instagram_handle",
            "status",
            "rejection_reason",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields


class SellerPublicProfileSerializer(serializers.ModelSerializer):
    """Perfil público (AllowAny). Sin teléfono ni datos del usuario (LOPDP)."""

    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "venture_name",
            "description",
            "logo_url",
            "avg_rating",
            "reviews_count",
            "created_at",
        ]
        read_only_fields = fields


class SellerOwnProfileSerializer(serializers.ModelSerializer):
    """Perfil completo visible solo para el propio vendedor."""

    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "venture_name",
            "description",
            "logo_url",
            "contact_phone",
            "avg_rating",
            "reviews_count",
            "releases_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SellerProfileUpdateSerializer(serializers.Serializer):
    """logo_url/logo_public_id no son editables todavía (validación Cloudinary en Orden 4)."""

    venture_name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(max_length=1000, required=False)
    contact_phone = _phone_field(required=False)
