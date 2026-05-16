from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import AgentRun, AlarmCode, DiagnosisSession, Equipment, User
from app.schemas import (
    AgentRunResult,
    AgentStepRead,
    ChecklistRunRead,
    CreateDiagnosisSessionRequest,
    DiagnosisHypothesisRead,
    DiagnosisSessionListResponse,
    DiagnosisSessionRead,
    EvidenceLinkRead,
    InspectionPlanItemRead,
    ReportDraftRead,
)
from app.services.agent_engine import analyze_diagnosis_session
from app.services.audit import create_audit_event
from app.services.checklist_runner import ChecklistRunPreconditionError, create_checklist_run_from_latest_analysis
from app.services.report_builder import ReportPreconditionError, create_report_draft_from_session


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


@router.post("/{session_id}/analyze", response_model=AgentRunResult)
def analyze_diagnosis_session_endpoint(
    session_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> AgentRunResult:
    session = db.scalar(
        select(DiagnosisSession).where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.tenant_id == current_user.tenant_id,
        )
    )
    if session is None:
        _audit_cross_tenant_session_attempt(db, current_user, session_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis session not found")

    run = analyze_diagnosis_session(db, session=session, actor_user_id=current_user.id)
    db.commit()
    db.refresh(session)
    db.refresh(run)
    return _agent_run_response(run, session)


@router.post("/{session_id}/checklist-runs", response_model=ChecklistRunRead, status_code=status.HTTP_201_CREATED)
def create_checklist_run(
    session_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ChecklistRunRead:
    session = db.scalar(
        select(DiagnosisSession).where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.tenant_id == current_user.tenant_id,
        )
    )
    if session is None:
        _audit_cross_tenant_session_attempt(db, current_user, session_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis session not found")

    try:
        checklist_run = create_checklist_run_from_latest_analysis(
            db,
            diagnosis_session=session,
            actor_user_id=current_user.id,
        )
    except ChecklistRunPreconditionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(checklist_run)
    return ChecklistRunRead.model_validate(checklist_run)


@router.post("/{session_id}/report-drafts", response_model=ReportDraftRead, status_code=status.HTTP_201_CREATED)
def create_report_draft(
    session_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> ReportDraftRead:
    session = db.scalar(
        select(DiagnosisSession).where(
            DiagnosisSession.id == session_id,
            DiagnosisSession.tenant_id == current_user.tenant_id,
        )
    )
    if session is None:
        _audit_cross_tenant_session_attempt(db, current_user, session_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis session not found")

    try:
        report_draft = create_report_draft_from_session(
            db,
            diagnosis_session=session,
            actor_user_id=current_user.id,
        )
    except ReportPreconditionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(report_draft)
    return ReportDraftRead.model_validate(report_draft)


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


def _agent_run_response(run: AgentRun, session: DiagnosisSession) -> AgentRunResult:
    hypotheses = []
    evidence = []
    for hypothesis in sorted(run.hypotheses, key=lambda item: item.rank):
        links = sorted(hypothesis.evidence_links, key=lambda item: item.source_code)
        evidence.extend(
            EvidenceLinkRead(
                id=link.id,
                hypothesis_id=link.hypothesis_id,
                source_type=link.source_type,
                source_code=link.source_code,
                title=link.title,
                excerpt=link.excerpt,
                relevance_reason=link.relevance_reason,
            )
            for link in links
        )
        hypotheses.append(
            DiagnosisHypothesisRead(
                id=hypothesis.id,
                rank=hypothesis.rank,
                title=hypothesis.title,
                reasoning=hypothesis.reasoning,
                confidence_band=hypothesis.confidence_band,
                risk_level=hypothesis.risk_level,
                evidence_ids=[link.source_code for link in links],
                recommended_next_checks=hypothesis.recommended_next_checks,
            )
        )

    return AgentRunResult(
        run_id=run.id,
        session_id=run.session_id,
        status=run.status,
        mode=run.mode,
        safety_result=run.safety_result,
        risk_level=session.risk_level,
        steps=[
            AgentStepRead(
                id=step.id,
                step_order=step.step_order,
                name=step.name,
                status=step.status,
                summary=step.summary,
                details=step.details,
            )
            for step in sorted(run.steps, key=lambda item: item.step_order)
        ],
        hypotheses=hypotheses,
        evidence=evidence,
        inspection_plan_items=[
            InspectionPlanItemRead(
                id=item.id,
                item_order=item.item_order,
                title=item.title,
                instruction=item.instruction,
                expected_observation=item.expected_observation,
                safety_level=item.safety_level,
                evidence_codes=item.evidence_codes,
            )
            for item in sorted(run.inspection_plan_items, key=lambda item: item.item_order)
        ],
    )
