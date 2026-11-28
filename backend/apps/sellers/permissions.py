from rest_framework import status
from rest_framework.permissions import BasePermission

from apps.core.exceptions import DomainError


class IsActiveSeller(BasePermission):
    """Permite el acceso solo a usuarios autenticados con SellerProfile activo.

    Combinar después de IsAuthenticated: un anónimo recibe NOT_AUTHENTICATED y un usuario sin
    perfil activo recibe 403 NOT_A_SELLER (formato uniforme vía DomainError). Solo lectura.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if not user.is_seller:
            raise DomainError(
                "NOT_A_SELLER",
                "Necesitas un perfil de vendedor activo.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return True
