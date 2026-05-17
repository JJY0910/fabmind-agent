from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DiagnosisSession, Equipment, EquipmentAlarmEvent, EquipmentIncident, User
from app.services.audit import create_audit_event


INCIDENT_STATUSES = {
    "OPEN",
    "TRIAGED",
    "CHECKLIST_IN_PROGRESS",
    "REPORT_SUBMITTED",
    "APPROVED",
    "CLOSED",
    "CANCELLED",
}
TERMINAL_INCIDENT_STATUSES = {"CLOSED", "CANCELLED"}
FIELD_ALLOWED_STATUS_TARGETS = {"TRIAGED", "CHECKLIST_IN_PROGRESS"}
ALLOWED_TRANSITIONS = {
    "OPEN": {"TRIAGED", "CANCELLED"},
    "TRIAGED": {"CHECKLIST_IN_PROGRESS", "CANCELLED"},
    "CHECKLIST_IN_PROGRESS": {"REPORT_SUBMITTED", "CANCELLED"},
    "REPORT_SUBMITTED": {"APPROVED", "CANCELLED"},
    "APPROVED": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
logger = logging.getLogger(__name__)


class IncidentLifecycleError(ValueError):
    pass


class IncidentPermissionError(IncidentLifecycleError):
    pass


def create_incident_case(
    db: Session,
    *,
    actor: User,
    equipment: Equipment,
    title: str,
    summary: str,
    alarm_code: str,
    severity: str,
    primary_alarm_event_id: uuid.UUID | None = None,
    diagnosis_session_id: uuid.UUID | None = None,
    assigned_role: str | None = "FIELD_ENGINEER",
    incident_id: uuid.UUID | None = None,
) -> EquipmentIncident:
    incident_id = incident_id or uuid.uuid4()
    incident = EquipmentIncident(
        id=incident_id,
        tenant_id=actor.tenant_id,
        equipment_id=equipment.id,
        primary_alarm_event_id=primary_alarm_event_id,
        diagnosis_session_id=diagnosis_session_id,
        case_number=_case_number(equipment.code, alarm_code, incident_id),
        title=title,
        summary=summary,
        alarm_code=alarm_code,
        severity=severity,
        status="OPEN",
        owner_user_id=actor.id,
        assigned_role=assigned_role,
        equipment=equipment,
    )
    db.add(incident)
    db.flush()
    _audit_incident(
        db,
        actor=actor,
        incident=incident,
        event_type="INCIDENT_CREATED",
        payload={"equipment_code": equipment.code, "alarm_code": alarm_code, "severity": severity},
    )
    if primary_alarm_event_id is not None:
        _audit_incident(
            db,
            actor=actor,
            incident=incident,
            event_type="INCIDENT_LINKED_TO_ALARM_EVENT",
            payload={"alarm_event_id": str(primary_alarm_event_id), "alarm_code": alarm_code},
        )
    if diagnosis_session_id is not None:
        _audit_incident(
            db,
            actor=actor,
            incident=incident,
            event_type="INCIDENT_LINKED_TO_DIAGNOSIS",
            payload={"diagnosis_session_id": str(diagnosis_session_id)},
        )
    logger.info(
        "incident_created",
        extra={
            "incident_id": str(incident.id),
            "tenant_id": str(actor.tenant_id),
            "equipment_code": equipment.code,
            "alarm_code": alarm_code,
            "severity": severity,
        },
    )
    return incident


def create_incident_from_diagnosis_session(
    db: Session,
    *,
    actor: User,
    session: DiagnosisSession,
    equipment: Equipment,
) -> EquipmentIncident:
    existing = db.scalar(
        select(EquipmentIncident).where(
            EquipmentIncident.diagnosis_session_id == session.id,
            EquipmentIncident.tenant_id == actor.tenant_id,
        )
    )
    if existing is not None:
        return existing

    active_incident = db.scalar(
        select(EquipmentIncident)
        .where(
            EquipmentIncident.tenant_id == actor.tenant_id,
            EquipmentIncident.equipment_id == equipment.id,
            EquipmentIncident.alarm_code == session.alarm_code,
            EquipmentIncident.status.notin_(TERMINAL_INCIDENT_STATUSES),
        )
        .order_by(EquipmentIncident.updated_at.desc(), EquipmentIncident.opened_at.desc())
        .limit(1)
    )
    if active_incident is not None:
        if active_incident.diagnosis_session_id != session.id:
            active_incident.diagnosis_session_id = session.id
            active_incident.updated_at = datetime.now(UTC)
            _audit_incident(
                db,
                actor=actor,
                incident=active_incident,
                event_type="INCIDENT_LINKED_TO_DIAGNOSIS",
                payload={"diagnosis_session_id": str(session.id)},
            )
        active_incident.severity = _highest_severity(active_incident.severity, session.risk_level)
        return active_incident

    return create_incident_case(
        db,
        actor=actor,
        equipment=equipment,
        title=f"{equipment.code} {session.alarm_code}",
        summary=session.symptom_summary,
        alarm_code=session.alarm_code,
        severity=session.risk_level,
        diagnosis_session_id=session.id,
        incident_id=session.id,
    )


def create_or_link_incident_from_alarm_event(
    db: Session,
    *,
    actor: User,
    event: EquipmentAlarmEvent,
    equipment: Equipment,
) -> EquipmentIncident:
    incident = db.scalar(
        select(EquipmentIncident)
        .where(
            EquipmentIncident.tenant_id == actor.tenant_id,
            EquipmentIncident.equipment_id == equipment.id,
            EquipmentIncident.alarm_code == event.alarm_code,
            EquipmentIncident.status.notin_(TERMINAL_INCIDENT_STATUSES),
        )
        .order_by(EquipmentIncident.updated_at.desc(), EquipmentIncident.opened_at.desc())
        .limit(1)
    )
    if incident is not None:
        if incident.primary_alarm_event_id is None:
            incident.primary_alarm_event_id = event.id
            incident.updated_at = datetime.now(UTC)
            _audit_incident(
                db,
                actor=actor,
                incident=incident,
                event_type="INCIDENT_LINKED_TO_ALARM_EVENT",
                payload={"alarm_event_id": str(event.id), "alarm_code": event.alarm_code},
            )
        incident.severity = _highest_severity(incident.severity, event.severity)
        return incident

    return create_incident_case(
        db,
        actor=actor,
        equipment=equipment,
        title=f"{equipment.code} {event.alarm_code}",
        summary=event.alarm_name or "Read-only alarm event opened an operational incident.",
        alarm_code=event.alarm_code,
        severity=event.severity,
        primary_alarm_event_id=event.id,
    )


def transition_incident_status(
    db: Session,
    *,
    actor: User,
    incident: EquipmentIncident,
    target_status: str,
) -> EquipmentIncident:
    if target_status not in INCIDENT_STATUSES:
        raise IncidentLifecycleError("Unknown incident status")
    if incident.status == target_status:
        return incident

    if actor.role.code == "FIELD_ENGINEER" and target_status not in FIELD_ALLOWED_STATUS_TARGETS:
        _audit_incident(
            db,
            actor=actor,
            incident=incident,
            event_type="INCIDENT_UPDATE_DENIED",
            severity="SECURITY",
            payload={
                "reason": "role_not_allowed_for_status",
                "current_status": incident.status,
                "target_status": target_status,
                "role": actor.role.code,
            },
        )
        raise IncidentPermissionError("Incident status transition requires senior or admin role")

    allowed = ALLOWED_TRANSITIONS.get(incident.status, set())
    if target_status not in allowed:
        raise IncidentLifecycleError(f"Invalid incident status transition: {incident.status} -> {target_status}")

    previous_status = incident.status
    incident.status = target_status
    incident.updated_at = datetime.now(UTC)
    _apply_status_timestamp(incident, target_status)
    _audit_incident(
        db,
        actor=actor,
        incident=incident,
        event_type="INCIDENT_STATUS_CHANGED",
            payload={"from_status": previous_status, "to_status": target_status},
        )
    logger.info(
        "incident_status_changed",
        extra={
            "incident_id": str(incident.id),
            "tenant_id": str(incident.tenant_id),
            "from_status": previous_status,
            "to_status": target_status,
        },
    )
    if target_status == "CLOSED":
        _audit_incident(
            db,
            actor=actor,
            incident=incident,
            event_type="INCIDENT_CLOSED",
            payload={"from_status": previous_status, "to_status": target_status},
        )
    return incident


def _apply_status_timestamp(incident: EquipmentIncident, status: str) -> None:
    now = datetime.now(UTC)
    if status == "TRIAGED" and incident.triaged_at is None:
        incident.triaged_at = now
    elif status == "CHECKLIST_IN_PROGRESS" and incident.checklist_started_at is None:
        incident.checklist_started_at = now
    elif status == "REPORT_SUBMITTED" and incident.report_submitted_at is None:
        incident.report_submitted_at = now
    elif status == "APPROVED" and incident.approved_at is None:
        incident.approved_at = now
    elif status == "CLOSED" and incident.closed_at is None:
        incident.closed_at = now


def _audit_incident(
    db: Session,
    *,
    actor: User,
    incident: EquipmentIncident,
    event_type: str,
    severity: str = "INFO",
    payload: dict[str, object] | None = None,
) -> None:
    create_audit_event(
        db,
        tenant_id=incident.tenant_id,
        actor_user_id=actor.id,
        event_type=event_type,
        resource_type="equipment_incident",
        resource_id=incident.id,
        severity=severity,
        payload=payload or {},
    )
    if event_type.startswith("INCIDENT_LINKED"):
        logger.info(
            "incident_linked",
            extra={
                "incident_id": str(incident.id),
                "tenant_id": str(incident.tenant_id),
                "event_type": event_type,
            },
        )


def _case_number(equipment_code: str, alarm_code: str, incident_id: uuid.UUID | None) -> str:
    suffix = str(incident_id or uuid.uuid4()).replace("-", "")[:10].upper()
    raw = f"INC-{equipment_code}-{alarm_code}-{suffix}"
    return raw[:80]


def _highest_severity(current: str, candidate: str) -> str:
    if SEVERITY_RANK.get(candidate, 0) > SEVERITY_RANK.get(current, 0):
        return candidate
    return current
