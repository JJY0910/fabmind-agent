from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import ChecklistItem, ChecklistRun, User
from app.schemas import ChecklistRunRead, UpdateChecklistItemRequest
from app.services.audit import create_audit_event
from app.services.checklist_runner import update_checklist_item


READ_WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/checklist-runs", tags=["checklist-runs"])


@router.get("/{checklist_run_id}", response_model=ChecklistRunRead)
def get_checklist_run(
    checklist_run_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ChecklistRunRead:
    checklist_run = _get_tenant_checklist_run_or_404(db, current_user, checklist_run_id)
    return ChecklistRunRead.model_validate(checklist_run)


@router.patch("/{checklist_run_id}/items/{item_id}", response_model=ChecklistRunRead)
def update_checklist_run_item(
    checklist_run_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: UpdateChecklistItemRequest,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ChecklistRunRead:
    checklist_run = _get_tenant_checklist_run_or_404(db, current_user, checklist_run_id)
    item = db.scalar(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id,
            ChecklistItem.checklist_run_id == checklist_run.id,
            ChecklistItem.tenant_id == current_user.tenant_id,
        )
    )
    if item is None:
        _audit_cross_tenant_item_attempt(db, current_user, item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found")

    update_checklist_item(
        db,
        checklist_run=checklist_run,
        item=item,
        actor_user_id=current_user.id,
        status=payload.status,
        field_note=payload.field_note,
    )
    db.commit()
    db.refresh(checklist_run)
    return ChecklistRunRead.model_validate(checklist_run)


def _get_tenant_checklist_run_or_404(
    db: Session,
    current_user: User,
    checklist_run_id: uuid.UUID,
) -> ChecklistRun:
    checklist_run = db.scalar(
        select(ChecklistRun).where(
            ChecklistRun.id == checklist_run_id,
            ChecklistRun.tenant_id == current_user.tenant_id,
        )
    )
    if checklist_run is not None:
        return checklist_run

    _audit_cross_tenant_run_attempt(db, current_user, checklist_run_id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist run not found")


def _audit_cross_tenant_run_attempt(db: Session, current_user: User, checklist_run_id: uuid.UUID) -> None:
    checklist_run = db.scalar(select(ChecklistRun).where(ChecklistRun.id == checklist_run_id))
    if checklist_run is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="CHECKLIST_RUN_ACCESS_DENIED",
        resource_type="checklist_run",
        resource_id=checklist_run_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()


def _audit_cross_tenant_item_attempt(db: Session, current_user: User, item_id: uuid.UUID) -> None:
    item = db.scalar(select(ChecklistItem).where(ChecklistItem.id == item_id))
    if item is None or item.tenant_id == current_user.tenant_id:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="CHECKLIST_ITEM_ACCESS_DENIED",
        resource_type="checklist_item",
        resource_id=item_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
