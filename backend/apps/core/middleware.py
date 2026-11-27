"""Anti-bypass: toda petición a /api/v1/* debe llegar a través del proxy de Cloudflare."""

import hmac

from django.conf import settings
from django.http import JsonResponse

from apps.core.exceptions import error_payload

HEALTH_PATHS = frozenset({"/api/v1/health/", "/api/health/"})
CRON_PATH = "/api/v1/cron/sweep/"
API_PREFIX = "/api/v1/"
ADMIN_PREFIX = "/admin/"


def _secret_matches(provided: str, expected: str) -> bool:
    """Comparación en tiempo constante; falla cerrado si el secreto esperado está vacío."""
    if not expected:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


class InternalProxyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        if path in HEALTH_PATHS or path.startswith(ADMIN_PREFIX):
            return self.get_response(request)

        if path == CRON_PATH:
            provided = request.headers.get("X-Cron-Secret", "")
            if not _secret_matches(provided, settings.CRON_SECRET):
                return JsonResponse(
                    error_payload("UNAUTHORIZED", "Cron secret inválido."), status=403
                )
            return self.get_response(request)

        if path.startswith(API_PREFIX):
            provided = request.headers.get("X-Internal-Proxy-Secret", "")
            if not _secret_matches(provided, settings.INTERNAL_PROXY_SECRET):
                return JsonResponse(
                    error_payload("FORBIDDEN_PROXY", "Acceso directo no permitido."), status=403
                )

        return self.get_response(request)
