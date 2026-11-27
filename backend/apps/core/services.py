import uuid
from typing import Any

from apps.core.models import AuditLog


def record_audit(
    *,
    actor,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Inserta una entrada en AuditLog. Debe invocarse dentro de la transacción del caso de uso.

    `metadata` nunca debe contener datos personales (LOPDP).
    """
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata or {},
    )
