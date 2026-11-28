"""El enum ErrorCode (publicado en OpenAPI) cubre todos los códigos que la API puede emitir."""

import re
from pathlib import Path

from apps.core.exceptions import ErrorCode
from apps.core.serializers import ErrorResponseSerializer

APPS_DIR = Path(__file__).resolve().parents[2]
_DOMAIN_ERROR_RE = re.compile(r'DomainError\(\s*"([A-Z_]+)"')
_PAYLOAD_RE = re.compile(r'error_payload\(\s*"([A-Z_]+)"')


def _codes_in_source() -> set[str]:
    codes: set[str] = set()
    for path in APPS_DIR.rglob("*.py"):
        if "tests" in path.parts or "migrations" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        codes |= set(_DOMAIN_ERROR_RE.findall(text)) | set(_PAYLOAD_RE.findall(text))
    return codes


def test_every_emitted_code_is_declared_in_error_code_enum():
    codes = _codes_in_source()
    assert codes, "La búsqueda de códigos no encontró nada"
    assert codes - set(ErrorCode.values) == set()


def test_error_response_code_is_an_enum():
    field = ErrorResponseSerializer().fields["code"]
    assert set(field.choices) == set(ErrorCode.values)
    for code in ("OTP_INVALID", "OTP_LOCKED", "OTP_RATE_LIMITED", "ALREADY_A_SELLER"):
        assert code in field.choices
