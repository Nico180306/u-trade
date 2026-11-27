from rest_framework.throttling import ScopedRateThrottle

CLIENT_IP_HEADER = "HTTP_X_CLIENT_IP"
UNKNOWN_CLIENT = "unknown"


class ClientIPRateThrottle(ScopedRateThrottle):
    """Throttle por `throttle_scope` de la vista, identificando SIEMPRE por X-Client-IP.

    X-Client-IP solo es confiable porque InternalProxyMiddleware ya validó el secreto del proxy.
    Si la cabecera falta, todas esas peticiones comparten el bucket "unknown" (sin bypass).
    """

    def get_cache_key(self, request, view):
        ident = request.META.get(CLIENT_IP_HEADER, "").strip() or UNKNOWN_CLIENT
        return self.cache_format % {"scope": self.scope, "ident": ident}
