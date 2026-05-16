from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import DiagnosisSession, Equipment, ReportDraft, User
from app.schemas import ReportApprovalRequest, ReportDraftListResponse, ReportDraftRead, ReportDraftSummary, ReportRejectionRequest
from app.services.audit import create_audit_event
from app.services.report_builder import ReportPreconditionError, decide_report_draft, submit_report_draft


READ_WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
APPROVAL_ROLES = (ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/report-drafts", tags=["report-drafts"])


@router.get("", response_model=ReportDraftListResponse)
def list_report_drafts(
    status_filter: str | None = Query(default=None, alias="status"),
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftListResponse:
    filters = [ReportDraft.tenant_id == current_user.tenant_id]
    if status_filter:
        filters.append(ReportDraft.status == status_filter)
    if equipment_id:
        filters.append(DiagnosisSession.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)

    total = (
        db.scalar(
            select(func.count())
            .select_from(ReportDraft)
            .join(DiagnosisSession, ReportDraft.diagnosis_session_id == DiagnosisSession.id)
            .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    reports = (
        db.execute(
            select(ReportDraft)
            .join(DiagnosisSession, ReportDraft.diagnosis_session_id == DiagnosisSession.id)
            .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
            .options(
                joinedload(ReportDraft.diagnosis_session).joinedload(DiagnosisSession.equipment),
                joinedload(ReportDraft.created_by),
            )
            .where(*filters)
            .order_by(ReportDraft.updated_at.desc(), ReportDraft.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .scalars()
        .all()
    )
    return ReportDraftListResponse(
        items=[_report_draft_summary(report) for report in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


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


def _report_draft_summary(report: ReportDraft) -> ReportDraftSummary:
    return ReportDraftSummary(
        report_draft_id=report.id,
        diagnosis_session_id=report.diagnosis_session_id,
        equipment_code=report.diagnosis_session.equipment.code,
        status=report.status,
        root_cause_summary=report.root_cause,
        created_by=report.created_by.display_name,
        created_at=report.created_at,
        updated_at=report.updated_at,
        submitted_at=report.updated_at if report.status in {"SUBMITTED", "APPROVED", "REJECTED"} else None,
    )
