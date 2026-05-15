from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def create_audit_event(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    event_type: str,
    resource_type: str,
    severity: str = "INFO",
    actor_user_id: uuid.UUID | None = None,
    resource_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=severity,
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event

