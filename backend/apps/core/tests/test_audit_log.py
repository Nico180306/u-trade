import uuid

import pytest

from apps.core.models import AuditLog, ImmutableAuditLogError
from apps.core.services import record_audit

pytestmark = pytest.mark.django_db


def test_record_audit_creates_entry(user):
    entry = record_audit(
        actor=user, action="TEST_ACTION", entity_type="User", entity_id=user.id, metadata={"a": 1}
    )

    stored = AuditLog.objects.get(pk=entry.pk)
    assert isinstance(stored.id, uuid.UUID)
    assert stored.actor == user
    assert stored.metadata == {"a": 1}
    assert stored.created_at.utcoffset().total_seconds() == 0


def test_audit_log_cannot_be_updated(user):
    entry = record_audit(actor=user, action="X", entity_type="User", entity_id=user.id)
    entry.action = "Y"

    with pytest.raises(ImmutableAuditLogError):
        entry.save()


def test_audit_log_cannot_be_deleted(user):
    entry = record_audit(actor=user, action="X", entity_type="User", entity_id=user.id)

    with pytest.raises(ImmutableAuditLogError):
        entry.delete()
    assert AuditLog.objects.filter(pk=entry.pk).exists()
