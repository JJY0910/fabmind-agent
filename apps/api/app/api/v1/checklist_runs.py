from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import ChecklistItem, ChecklistRun, DiagnosisSession, Equipment, User
from app.schemas import ChecklistRunListResponse, ChecklistRunRead, ChecklistRunSummary, UpdateChecklistItemRequest
from app.services.audit import create_audit_event
from app.services.checklist_runner import update_checklist_item


READ_WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/checklist-runs", tags=["checklist-runs"])


@router.get("", response_model=ChecklistRunListResponse)
def list_checklist_runs(
    status_filter: str | None = Query(default=None, alias="status"),
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    diagnosis_session_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ChecklistRunListResponse:
    filters = [ChecklistRun.tenant_id == current_user.tenant_id]
    if status_filter:
        filters.append(ChecklistRun.status == status_filter)
    if diagnosis_session_id:
        filters.append(ChecklistRun.diagnosis_session_id == diagnosis_session_id)
    if equipment_id:
        filters.append(DiagnosisSession.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)

    total = (
        db.scalar(
            select(func.count())
            .select_from(ChecklistRun)
            .join(DiagnosisSession, ChecklistRun.diagnosis_session_id == DiagnosisSession.id)
            .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    checklist_runs = (
        db.execute(
            select(ChecklistRun)
            .join(DiagnosisSession, ChecklistRun.diagnosis_session_id == DiagnosisSession.id)
            .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
            .options(
                joinedload(ChecklistRun.items),
                joinedload(ChecklistRun.diagnosis_session).joinedload(DiagnosisSession.equipment),
            )
            .where(*filters)
            .order_by(ChecklistRun.updated_at.desc(), ChecklistRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .scalars()
        .all()
    )
    return ChecklistRunListResponse(
        items=[_checklist_run_summary(checklist_run) for checklist_run in checklist_runs],
        total=total,
        limit=limit,
        offset=offset,
    )


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


def _checklist_run_summary(checklist_run: ChecklistRun) -> ChecklistRunSummary:
    items = checklist_run.items
    completed_items = sum(1 for item in items if item.status in {"DONE", "SKIPPED"})
    failed_items = sum(1 for item in items if item.status == "BLOCKED")
    pending_items = sum(1 for item in items if item.status in {"TODO", "IN_PROGRESS"})
    equipment_code = checklist_run.diagnosis_session.equipment.code
    return ChecklistRunSummary(
        checklist_run_id=checklist_run.id,
        diagnosis_session_id=checklist_run.diagnosis_session_id,
        equipment_code=equipment_code,
        checklist_name=f"{equipment_code} inspection checklist",
        status=checklist_run.status,
        total_items=len(items),
        completed_items=completed_items,
        failed_items=failed_items,
        pending_items=pending_items,
        created_at=checklist_run.created_at,
        updated_at=checklist_run.updated_at,
    )
