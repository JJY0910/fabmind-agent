from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import AuditEvent, User
from app.schemas import AuditEventListResponse, AuditEventRead
from app.services.audit import create_audit_event


router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    event_type: str | None = None,
    severity: str | None = None,
    resource_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_roles(ROLE_SENIOR, ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> AuditEventListResponse:
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="AUDIT_CONSOLE_ACCESSED",
        resource_type="audit_events",
        severity="INFO",
        payload={
            "filters": {
                "event_type": event_type,
                "severity": severity,
                "resource_type": resource_type,
            },
            "limit": limit,
        },
    )
    db.commit()

    query = select(AuditEvent).where(AuditEvent.tenant_id == current_user.tenant_id)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if severity:
        query = query.where(AuditEvent.severity == severity)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)

    events = db.scalars(query.order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return AuditEventListResponse(items=[AuditEventRead.model_validate(event) for event in events])
