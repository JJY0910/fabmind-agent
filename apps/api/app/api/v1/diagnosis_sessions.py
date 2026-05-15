from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import AlarmCode, DiagnosisSession, Equipment, User
from app.schemas import CreateDiagnosisSessionRequest, DiagnosisSessionListResponse, DiagnosisSessionRead
from app.services.audit import create_audit_event


READ_WRITE_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/diagnosis-sessions", tags=["diagnosis-sessions"])


@router.post("", response_model=DiagnosisSessionRead, status_code=status.HTTP_201_CREATED)
def create_diagnosis_session(
    payload: CreateDiagnosisSessionRequest,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> DiagnosisSessionRead:
    equipment = db.scalar(
        select(Equipment).where(Equipment.id == payload.equipment_id, Equipment.tenant_id == current_user.tenant_id)
    )
    if equipment is None:
        _audit_cross_tenant_equipment_attempt(db, current_user, payload.equipment_id)
        raise HTTPException(status_code=422, detail="Unknown equipment_id")

    alarm = db.scalar(
        select(AlarmCode).where(
            AlarmCode.tenant_id == current_user.tenant_id,
            AlarmCode.equipment_family_id == equipment.family_id,
            AlarmCode.code == payload.alarm_code,
        )
    )
    if alarm is None:
        raise HTTPException(status_code=422, detail="Unknown alarm_code")

    session = DiagnosisSession(
        tenant_id=current_user.tenant_id,
        equipment_id=equipment.id,
        created_by_user_id=current_user.id,
        alarm_code=payload.alarm_code,
        symptom_summary=payload.symptom_summary,
        log_excerpt=payload.log_excerpt,
        ethercat_state=payload.ethercat_state,
        io_snapshot=payload.io_snapshot,
        recent_action=payload.recent_action,
        status="CREATED",
        risk_level=payload.risk_level,
    )
    db.add(session)
    db.flush()
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="DIAGNOSIS_SESSION_CREATED",
        resource_type="diagnosis_session",
        resource_id=session.id,
        severity="INFO",
        payload={"equipment_id": str(equipment.id), "alarm_code": payload.alarm_code},
    )
    db.commit()
    db.refresh(session)
    return DiagnosisSessionRead.model_validate(session)


@router.get("", response_model=DiagnosisSessionListResponse)
def list_diagnosis_sessions(
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> DiagnosisSessionListResponse:
    sessions = db.scalars(
        select(DiagnosisSession)
        .where(DiagnosisSession.tenant_id == current_user.tenant_id)
        .order_by(DiagnosisSession.created_at.desc())
    ).all()
    return DiagnosisSessionListResponse(items=[DiagnosisSessionRead.model_validate(item) for item in sessions])


@router.get("/{session_id}", response_model=DiagnosisSessionRead)
def get_diagnosis_session(
    session_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> DiagnosisSessionRead:
    session = db.scalar(
        select(DiagnosisSession).where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.tenant_id == current_user.tenant_id,
        )
    )
    if session is None:
        _audit_cross_tenant_session_attempt(db, current_user, session_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis session not found")

    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="DIAGNOSIS_SESSION_VIEWED",
        resource_type="diagnosis_session",
        resource_id=session.id,
        severity="INFO",
        payload={"equipment_id": str(session.equipment_id), "alarm_code": session.alarm_code},
    )
    db.commit()
    db.refresh(session)
    return DiagnosisSessionRead.model_validate(session)


def _audit_cross_tenant_equipment_attempt(db: Session, current_user: User, equipment_id: uuid.UUID) -> None:
    equipment = db.scalar(select(Equipment).where(Equipment.id == equipment_id))
    if equipment is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="DIAGNOSIS_EQUIPMENT_ACCESS_DENIED",
        resource_type="equipment",
        resource_id=equipment_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()


def _audit_cross_tenant_session_attempt(db: Session, current_user: User, session_id: uuid.UUID) -> None:
    session = db.scalar(select(DiagnosisSession).where(DiagnosisSession.id == session_id))
    if session is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="DIAGNOSIS_SESSION_ACCESS_DENIED",
        resource_type="diagnosis_session",
        resource_id=session_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
