"""Validación de formato y serialización. Sin reglas de negocio (viven en services.py)."""

from rest_framework import serializers

from apps.accounts.models import User


def _password_field() -> serializers.CharField:
    return serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128, style={"input_type": "password"}
    )


class UserMeSerializer(serializers.ModelSerializer):
    is_email_verified = serializers.BooleanField(read_only=True)
    is_uisek_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "email_verified_at",
            "uisek_email",
            "uisek_email_verified_at",
            "is_email_verified",
            "is_uisek_verified",
            "is_staff",
            "created_at",
        ]
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = _password_field()
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    accept_terms = serializers.BooleanField()
    accept_privacy = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = _password_field()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = _password_field()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = _password_field()
    new_password = _password_field()


class AccountDeleteSerializer(serializers.Serializer):
    current_password = _password_field()
