from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, require_roles
from app.db.session import get_db
from app.models import AuditEvent, User
from app.schemas import AuditEventListResponse, AuditEventRead


router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    event_type: str | None = None,
    severity: str | None = None,
    current_user: User = Depends(require_roles(ROLE_ADMIN)),
    db: Session = Depends(get_db),
) -> AuditEventListResponse:
    query = select(AuditEvent).where(AuditEvent.tenant_id == current_user.tenant_id)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if severity:
        query = query.where(AuditEvent.severity == severity)

    events = db.scalars(query.order_by(AuditEvent.created_at.desc())).all()
    return AuditEventListResponse(items=[AuditEventRead.model_validate(event) for event in events])

