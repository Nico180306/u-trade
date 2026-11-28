import re

from rest_framework.throttling import ScopedRateThrottle

CLIENT_IP_HEADER = "HTTP_X_CLIENT_IP"
UNKNOWN_CLIENT = "unknown"

_PERIOD_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_RATE_RE = re.compile(r"^(?P<num>\d+)/(?P<mult>\d*)(?P<unit>[smhd])")


class ClientIPRateThrottle(ScopedRateThrottle):
    """Throttle por `throttle_scope` de la vista, identificando SIEMPRE por X-Client-IP.

    X-Client-IP solo es confiable porque InternalProxyMiddleware ya validó el secreto del proxy.
    Si la cabecera falta, todas esas peticiones comparten el bucket "unknown" (sin bypass).

    Además de las tasas DRF ("10/minute"), acepta un multiplicador de periodo ("3/15m").
    """

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        match = _RATE_RE.match(rate)
        if match is None:
            raise ValueError(f"Tasa de throttling inválida: {rate!r}")
        multiplier = int(match["mult"] or 1)
        return int(match["num"]), multiplier * _PERIOD_SECONDS[match["unit"]]

    def get_cache_key(self, request, view):
        ident = request.META.get(CLIENT_IP_HEADER, "").strip() or UNKNOWN_CLIENT
        return self.cache_format % {"scope": self.scope, "ident": ident}
