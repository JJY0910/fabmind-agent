from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import (
    ChecklistRun,
    DiagnosisSession,
    Equipment,
    EquipmentAlarmEvent,
    EquipmentIncident,
    ReportApproval,
    ReportDraft,
    User,
)
from app.schemas import (
    CreateIncidentRequest,
    IncidentListResponse,
    IncidentSummary,
    UpdateIncidentLinksRequest,
    UpdateIncidentStatusRequest,
)
from app.services.audit import create_audit_event
from app.services.incidents import IncidentLifecycleError, IncidentPermissionError, create_incident_case, transition_incident_status


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    severity: str | None = None,
    risk_level: str | None = None,
    alarm_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    filters = [EquipmentIncident.tenant_id == current_user.tenant_id]
    if status_filter:
        filters.append(EquipmentIncident.status == status_filter)
    if equipment_id:
        filters.append(EquipmentIncident.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)
    if severity or risk_level:
        filters.append(EquipmentIncident.severity == (severity or risk_level))
    if alarm_code:
        filters.append(EquipmentIncident.alarm_code == alarm_code)

    total = (
        db.scalar(
            select(func.count())
            .select_from(EquipmentIncident)
            .join(Equipment, EquipmentIncident.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    incidents = (
        db.execute(
            select(EquipmentIncident)
            .join(Equipment, EquipmentIncident.equipment_id == Equipment.id)
            .options(joinedload(EquipmentIncident.equipment), joinedload(EquipmentIncident.owner))
            .where(*filters)
            .order_by(EquipmentIncident.updated_at.desc(), EquipmentIncident.opened_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .unique()
        .scalars()
        .all()
    )
    return IncidentListResponse(
        items=[_incident_summary(item) for item in incidents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=IncidentSummary, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: CreateIncidentRequest,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentSummary:
    equipment = _resolve_equipment(db, current_user, payload.equipment_id, payload.equipment_code)
    primary_alarm_event = _resolve_alarm_event(db, current_user, payload.primary_alarm_event_id, equipment.id)
    diagnosis_session = _resolve_diagnosis_session(db, current_user, payload.diagnosis_session_id, equipment.id)
    incident = create_incident_case(
        db,
        actor=current_user,
        equipment=equipment,
        title=payload.title,
        summary=payload.summary,
        alarm_code=payload.alarm_code,
        severity=payload.severity,
        primary_alarm_event_id=primary_alarm_event.id if primary_alarm_event is not None else None,
        diagnosis_session_id=diagnosis_session.id if diagnosis_session is not None else None,
        assigned_role=payload.assigned_role,
    )
    db.commit()
    db.refresh(incident)
    return _incident_summary(incident)


@router.get("/{incident_id}", response_model=IncidentSummary)
def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentSummary:
    incident = _get_tenant_incident_or_404(db, current_user, incident_id)
    return _incident_summary(incident)


@router.patch("/{incident_id}/status", response_model=IncidentSummary)
def update_incident_status(
    incident_id: uuid.UUID,
    payload: UpdateIncidentStatusRequest,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentSummary:
    incident = _get_tenant_incident_or_404(db, current_user, incident_id)
    try:
        transition_incident_status(db, actor=current_user, incident=incident, target_status=payload.status)
    except IncidentPermissionError as exc:
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except IncidentLifecycleError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(incident)
    return _incident_summary(incident)


@router.patch("/{incident_id}/links", response_model=IncidentSummary)
def update_incident_links(
    incident_id: uuid.UUID,
    payload: UpdateIncidentLinksRequest,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> IncidentSummary:
    incident = _get_tenant_incident_or_404(db, current_user, incident_id)
    linked_events: list[tuple[str, str, uuid.UUID]] = []

    if payload.diagnosis_session_id is not None:
        diagnosis_session = _resolve_diagnosis_session(db, current_user, payload.diagnosis_session_id, incident.equipment_id)
        if incident.diagnosis_session_id != diagnosis_session.id:
            incident.diagnosis_session_id = diagnosis_session.id
            linked_events.append(("INCIDENT_LINKED_TO_DIAGNOSIS", "diagnosis_session_id", diagnosis_session.id))
    if payload.checklist_run_id is not None:
        checklist_run = _resolve_checklist_run(db, current_user, payload.checklist_run_id, incident.equipment_id)
        if incident.checklist_run_id != checklist_run.id:
            incident.checklist_run_id = checklist_run.id
            if incident.checklist_started_at is None:
                incident.checklist_started_at = checklist_run.created_at
            linked_events.append(("INCIDENT_LINKED_TO_CHECKLIST", "checklist_run_id", checklist_run.id))
    if payload.report_draft_id is not None:
        report_draft = _resolve_report_draft(db, current_user, payload.report_draft_id, incident.equipment_id)
        if incident.report_draft_id != report_draft.id:
            incident.report_draft_id = report_draft.id
            if report_draft.status in {"SUBMITTED", "APPROVED", "REJECTED"} and incident.report_submitted_at is None:
                incident.report_submitted_at = report_draft.updated_at
            linked_events.append(("INCIDENT_LINKED_TO_REPORT", "report_draft_id", report_draft.id))
    if payload.approval_id is not None:
        approval = _resolve_approval(db, current_user, payload.approval_id, incident.equipment_id)
        if incident.approval_id != approval.id:
            incident.approval_id = approval.id
            if approval.decision == "APPROVED" and incident.approved_at is None:
                incident.approved_at = approval.decided_at
            linked_events.append(("INCIDENT_LINKED_TO_APPROVAL", "approval_id", approval.id))

    for event_type, key, resource_id in linked_events:
        create_audit_event(
            db,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
            event_type=event_type,
            resource_type="equipment_incident",
            resource_id=incident.id,
            severity="INFO",
            payload={key: str(resource_id)},
        )
    db.commit()
    db.refresh(incident)
    return _incident_summary(incident)


def _get_tenant_incident_or_404(db: Session, current_user: User, incident_id: uuid.UUID) -> EquipmentIncident:
    incident = db.scalar(
        select(EquipmentIncident)
        .options(joinedload(EquipmentIncident.equipment), joinedload(EquipmentIncident.owner))
        .where(EquipmentIncident.id == incident_id, EquipmentIncident.tenant_id == current_user.tenant_id)
    )
    if incident is not None:
        return incident

    _audit_cross_tenant_incident_attempt(db, current_user, incident_id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


def _resolve_equipment(
    db: Session,
    current_user: User,
    equipment_id: uuid.UUID | None,
    equipment_code: str | None,
) -> Equipment:
    if equipment_id is None and equipment_code is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="equipment_id or equipment_code is required")

    filters = [Equipment.tenant_id == current_user.tenant_id]
    if equipment_id is not None:
        filters.append(Equipment.id == equipment_id)
    if equipment_code is not None:
        filters.append(Equipment.code == equipment_code)
    equipment = db.scalar(select(Equipment).where(*filters))
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return equipment


def _resolve_alarm_event(
    db: Session,
    current_user: User,
    alarm_event_id: uuid.UUID | None,
    equipment_id: uuid.UUID,
) -> EquipmentAlarmEvent | None:
    if alarm_event_id is None:
        return None
    event = db.scalar(
        select(EquipmentAlarmEvent).where(
            EquipmentAlarmEvent.id == alarm_event_id,
            EquipmentAlarmEvent.tenant_id == current_user.tenant_id,
            EquipmentAlarmEvent.equipment_id == equipment_id,
        )
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alarm event not found")
    return event


def _resolve_diagnosis_session(
    db: Session,
    current_user: User,
    diagnosis_session_id: uuid.UUID | None,
    equipment_id: uuid.UUID,
) -> DiagnosisSession | None:
    if diagnosis_session_id is None:
        return None
    session = db.scalar(
        select(DiagnosisSession).where(
            DiagnosisSession.id == diagnosis_session_id,
            DiagnosisSession.tenant_id == current_user.tenant_id,
            DiagnosisSession.equipment_id == equipment_id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis session not found")
    return session


def _resolve_checklist_run(
    db: Session,
    current_user: User,
    checklist_run_id: uuid.UUID,
    equipment_id: uuid.UUID,
) -> ChecklistRun:
    checklist_run = db.scalar(
        select(ChecklistRun)
        .join(DiagnosisSession, ChecklistRun.diagnosis_session_id == DiagnosisSession.id)
        .where(
            ChecklistRun.id == checklist_run_id,
            ChecklistRun.tenant_id == current_user.tenant_id,
            DiagnosisSession.equipment_id == equipment_id,
        )
    )
    if checklist_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist run not found")
    return checklist_run


def _resolve_report_draft(
    db: Session,
    current_user: User,
    report_draft_id: uuid.UUID,
    equipment_id: uuid.UUID,
) -> ReportDraft:
    report = db.scalar(
        select(ReportDraft)
        .join(DiagnosisSession, ReportDraft.diagnosis_session_id == DiagnosisSession.id)
        .where(
            ReportDraft.id == report_draft_id,
            ReportDraft.tenant_id == current_user.tenant_id,
            DiagnosisSession.equipment_id == equipment_id,
        )
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report draft not found")
    return report


def _resolve_approval(
    db: Session,
    current_user: User,
    approval_id: uuid.UUID,
    equipment_id: uuid.UUID,
) -> ReportApproval:
    approval = db.scalar(
        select(ReportApproval)
        .join(ReportDraft, ReportApproval.report_draft_id == ReportDraft.id)
        .join(DiagnosisSession, ReportDraft.diagnosis_session_id == DiagnosisSession.id)
        .where(
            ReportApproval.id == approval_id,
            ReportApproval.tenant_id == current_user.tenant_id,
            DiagnosisSession.equipment_id == equipment_id,
        )
    )
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return approval


def _incident_summary(incident: EquipmentIncident) -> IncidentSummary:
    return IncidentSummary(
        incident_id=incident.id,
        equipment_id=incident.equipment_id,
        equipment_code=incident.equipment.code,
        case_number=incident.case_number,
        primary_alarm_event_id=incident.primary_alarm_event_id,
        alarm_code=incident.alarm_code,
        title=incident.title,
        summary=incident.summary,
        risk_level=incident.severity,
        status=incident.status,
        opened_at=incident.opened_at,
        updated_at=incident.updated_at,
        triaged_at=incident.triaged_at,
        checklist_started_at=incident.checklist_started_at,
        report_submitted_at=incident.report_submitted_at,
        approved_at=incident.approved_at,
        closed_at=incident.closed_at,
        owner=incident.owner.display_name if incident.owner is not None else None,
        assigned_role=incident.assigned_role,
        diagnosis_session_id=incident.diagnosis_session_id,
        linked_checklist_run_id=incident.checklist_run_id,
        linked_report_draft_id=incident.report_draft_id,
        linked_approval_id=incident.approval_id,
    )


def _audit_cross_tenant_incident_attempt(db: Session, current_user: User, incident_id: uuid.UUID) -> None:
    incident = db.scalar(select(EquipmentIncident).where(EquipmentIncident.id == incident_id))
    if incident is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="INCIDENT_ACCESS_DENIED",
        resource_type="equipment_incident",
        resource_id=incident_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
