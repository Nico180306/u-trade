import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """Base abstracta: PK UUIDv4 y timestamps en UTC."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ImmutableAuditLogError(Exception):
    """AuditLog es append-only: no se permite UPDATE ni DELETE desde la aplicación."""


class AuditLog(models.Model):
    """Registro inmutable de acciones relevantes.

    La inmutabilidad se refuerza aquí a nivel ORM; el `REVOKE UPDATE, DELETE` sobre el rol SQL
    de la aplicación se aplica en feature/prod-hardening.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="auditlog_entity_idx"),
            models.Index(fields=["actor", "created_at"], name="auditlog_actor_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableAuditLogError("AuditLog no admite modificaciones.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableAuditLogError("AuditLog no admite eliminaciones.")
