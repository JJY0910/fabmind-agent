from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import ChecklistRun, DiagnosisSession, Equipment, ReportDraft, User
from app.schemas import IncidentListResponse, IncidentSummary
from app.services.audit import create_audit_event


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
RAW_INCIDENT_STATUSES = {"CREATED", "ANALYZING", "ANALYSIS_READY", "INSUFFICIENT_EVIDENCE", "CLOSED"}

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    risk_level: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    filters = [DiagnosisSession.tenant_id == current_user.tenant_id]
    if equipment_id:
        filters.append(DiagnosisSession.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)
    if risk_level:
        filters.append(DiagnosisSession.risk_level == risk_level)
    if status_filter in RAW_INCIDENT_STATUSES:
        filters.append(DiagnosisSession.status == status_filter)

    total = (
        db.scalar(
            select(func.count())
            .select_from(DiagnosisSession)
            .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    sessions = db.scalars(
        select(DiagnosisSession)
        .join(Equipment, DiagnosisSession.equipment_id == Equipment.id)
        .options(joinedload(DiagnosisSession.equipment), joinedload(DiagnosisSession.created_by))
        .where(*filters)
        .order_by(DiagnosisSession.updated_at.desc(), DiagnosisSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    latest_checklists = _latest_checklists_by_session(db, current_user.tenant_id, [item.id for item in sessions])
    latest_reports = _latest_reports_by_session(db, current_user.tenant_id, [item.id for item in sessions])
    items = [
        _incident_summary(session, latest_checklists.get(session.id), latest_reports.get(session.id))
        for session in sessions
    ]
    if status_filter and status_filter not in RAW_INCIDENT_STATUSES:
        items = [item for item in items if item.status == status_filter]
        total = len(items)

    return IncidentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{incident_id}", response_model=IncidentSummary)
def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentSummary:
    session = db.scalar(
        select(DiagnosisSession)
        .options(joinedload(DiagnosisSession.equipment), joinedload(DiagnosisSession.created_by))
        .where(DiagnosisSession.id == incident_id, DiagnosisSession.tenant_id == current_user.tenant_id)
    )
    if session is None:
        _audit_cross_tenant_incident_attempt(db, current_user, incident_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return _incident_summary(
        session,
        _latest_checklist_for_session(db, current_user.tenant_id, session.id),
        _latest_report_for_session(db, current_user.tenant_id, session.id),
    )


def _incident_summary(
    session: DiagnosisSession,
    checklist_run: ChecklistRun | None,
    report_draft: ReportDraft | None,
) -> IncidentSummary:
    updated_candidates = [session.updated_at]
    if checklist_run is not None:
        updated_candidates.append(checklist_run.updated_at)
    if report_draft is not None:
        updated_candidates.append(report_draft.updated_at)

    return IncidentSummary(
        incident_id=session.id,
        equipment_id=session.equipment_id,
        equipment_code=session.equipment.code,
        alarm_code=session.alarm_code,
        title=f"{session.equipment.code} {session.alarm_code}",
        summary=session.symptom_summary,
        risk_level=session.risk_level,
        status=_incident_status(session, checklist_run, report_draft),
        opened_at=session.created_at,
        updated_at=max(updated_candidates),
        owner=session.created_by.display_name,
        assigned_role="FIELD_ENGINEER",
        diagnosis_session_id=session.id,
        linked_checklist_run_id=checklist_run.id if checklist_run is not None else None,
        linked_report_draft_id=report_draft.id if report_draft is not None else None,
    )


def _incident_status(
    session: DiagnosisSession,
    checklist_run: ChecklistRun | None,
    report_draft: ReportDraft | None,
) -> str:
    if session.status == "CLOSED":
        return "CLOSED"
    if report_draft is not None:
        if report_draft.status == "SUBMITTED":
            return "AWAITING_APPROVAL"
        if report_draft.status == "APPROVED":
            return "RESOLVED"
        if report_draft.status == "REJECTED":
            return "REPORT_REJECTED"
    if checklist_run is not None:
        if checklist_run.status == "BLOCKED":
            return "BLOCKED"
        if checklist_run.status == "COMPLETED":
            return "CHECKLIST_COMPLETED"
        return "CHECKLIST_IN_PROGRESS"
    return session.status


def _latest_checklists_by_session(
    db: Session,
    tenant_id: uuid.UUID,
    session_ids: list[uuid.UUID],
) -> dict[uuid.UUID, ChecklistRun]:
    if not session_ids:
        return {}
    checklist_runs = db.scalars(
        select(ChecklistRun)
        .where(ChecklistRun.tenant_id == tenant_id, ChecklistRun.diagnosis_session_id.in_(session_ids))
        .order_by(ChecklistRun.updated_at.desc(), ChecklistRun.created_at.desc())
    ).all()
    latest: dict[uuid.UUID, ChecklistRun] = {}
    for checklist_run in checklist_runs:
        latest.setdefault(checklist_run.diagnosis_session_id, checklist_run)
    return latest


def _latest_reports_by_session(
    db: Session,
    tenant_id: uuid.UUID,
    session_ids: list[uuid.UUID],
) -> dict[uuid.UUID, ReportDraft]:
    if not session_ids:
        return {}
    reports = db.scalars(
        select(ReportDraft)
        .where(ReportDraft.tenant_id == tenant_id, ReportDraft.diagnosis_session_id.in_(session_ids))
        .order_by(ReportDraft.updated_at.desc(), ReportDraft.created_at.desc())
    ).all()
    latest: dict[uuid.UUID, ReportDraft] = {}
    for report in reports:
        latest.setdefault(report.diagnosis_session_id, report)
    return latest


def _latest_checklist_for_session(db: Session, tenant_id: uuid.UUID, session_id: uuid.UUID) -> ChecklistRun | None:
    return db.scalar(
        select(ChecklistRun)
        .where(ChecklistRun.tenant_id == tenant_id, ChecklistRun.diagnosis_session_id == session_id)
        .order_by(ChecklistRun.updated_at.desc(), ChecklistRun.created_at.desc())
        .limit(1)
    )


def _latest_report_for_session(db: Session, tenant_id: uuid.UUID, session_id: uuid.UUID) -> ReportDraft | None:
    return db.scalar(
        select(ReportDraft)
        .where(ReportDraft.tenant_id == tenant_id, ReportDraft.diagnosis_session_id == session_id)
        .order_by(ReportDraft.updated_at.desc(), ReportDraft.created_at.desc())
        .limit(1)
    )


def _audit_cross_tenant_incident_attempt(db: Session, current_user: User, incident_id: uuid.UUID) -> None:
    session = db.scalar(select(DiagnosisSession).where(DiagnosisSession.id == incident_id))
    if session is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="INCIDENT_ACCESS_DENIED",
        resource_type="incident",
        resource_id=incident_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
