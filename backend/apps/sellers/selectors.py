"""Consultas de solo lectura de vendedores."""

import uuid

from django.db.models import QuerySet

from apps.sellers.models import SellerApplication, SellerApplicationStatus, SellerProfile


def list_user_applications(user) -> QuerySet[SellerApplication]:
    return SellerApplication.objects.filter(user=user).order_by("-created_at")


def user_has_pending_application(user) -> bool:
    return SellerApplication.objects.filter(
        user=user, status=SellerApplicationStatus.PENDING
    ).exists()


def get_active_seller_profile_for_user(user) -> SellerProfile | None:
    return SellerProfile.objects.filter(user=user, is_active=True).first()


def get_public_seller_profile(profile_id: uuid.UUID) -> SellerProfile | None:
    return SellerProfile.objects.filter(pk=profile_id, is_active=True).first()
