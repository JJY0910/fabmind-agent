from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import ReportDraft, User
from app.schemas import ReportApprovalRequest, ReportDraftRead, ReportRejectionRequest
from app.services.audit import create_audit_event
from app.services.report_builder import ReportPreconditionError, decide_report_draft, submit_report_draft


READ_WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
APPROVAL_ROLES = (ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/report-drafts", tags=["report-drafts"])


@router.get("/{report_draft_id}", response_model=ReportDraftRead)
def get_report_draft(
    report_draft_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftRead:
    report = _get_tenant_report_or_404(db, current_user, report_draft_id)
    return ReportDraftRead.model_validate(report)


@router.post("/{report_draft_id}/submit", response_model=ReportDraftRead)
def submit_report_draft_endpoint(
    report_draft_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftRead:
    report = _get_tenant_report_or_404(db, current_user, report_draft_id)
    try:
        submit_report_draft(db, report_draft=report, actor_user_id=current_user.id)
    except ReportPreconditionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(report)
    return ReportDraftRead.model_validate(report)


@router.post("/{report_draft_id}/approve", response_model=ReportDraftRead)
def approve_report_draft(
    report_draft_id: uuid.UUID,
    payload: ReportApprovalRequest | None = Body(default=None),
    current_user: User = Depends(require_roles(*APPROVAL_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftRead:
    report = _get_tenant_report_or_404(db, current_user, report_draft_id)
    try:
        decide_report_draft(
            db,
            report_draft=report,
            actor_user_id=current_user.id,
            decision="APPROVED",
            comment=payload.comment if payload is not None else None,
        )
    except ReportPreconditionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(report)
    return ReportDraftRead.model_validate(report)


@router.post("/{report_draft_id}/reject", response_model=ReportDraftRead)
def reject_report_draft(
    report_draft_id: uuid.UUID,
    payload: ReportRejectionRequest,
    current_user: User = Depends(require_roles(*APPROVAL_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftRead:
    report = _get_tenant_report_or_404(db, current_user, report_draft_id)
    try:
        decide_report_draft(
            db,
            report_draft=report,
            actor_user_id=current_user.id,
            decision="REJECTED",
            comment=payload.comment,
        )
    except ReportPreconditionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(report)
    return ReportDraftRead.model_validate(report)


def _get_tenant_report_or_404(db: Session, current_user: User, report_draft_id: uuid.UUID) -> ReportDraft:
    report = db.scalar(
        select(ReportDraft).where(
            ReportDraft.id == report_draft_id,
            ReportDraft.tenant_id == current_user.tenant_id,
        )
    )
    if report is not None:
        return report

    _audit_cross_tenant_report_attempt(db, current_user, report_draft_id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report draft not found")


def _audit_cross_tenant_report_attempt(db: Session, current_user: User, report_draft_id: uuid.UUID) -> None:
    report = db.scalar(select(ReportDraft).where(ReportDraft.id == report_draft_id))
    if report is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="REPORT_DRAFT_ACCESS_DENIED",
        resource_type="report_draft",
        resource_id=report_draft_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
