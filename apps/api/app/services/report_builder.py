from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, ChecklistRun, DiagnosisSession, ReportApproval, ReportDraft
from app.services.audit import create_audit_event


VALID_CHECKLIST_STATUSES = {"COMPLETED", "BLOCKED"}


class ReportPreconditionError(ValueError):
    pass


def create_report_draft_from_session(
    db: Session,
    *,
    diagnosis_session: DiagnosisSession,
    actor_user_id: uuid.UUID,
) -> ReportDraft:
    agent_run = _latest_completed_agent_run(db, diagnosis_session)
    if agent_run is None:
        raise ReportPreconditionError("No completed agent analysis exists for this diagnosis session")

    checklist_run = _latest_valid_checklist_run(db, diagnosis_session, agent_run)
    if checklist_run is None:
        raise ReportPreconditionError("No completed or blocked checklist run exists for the latest completed agent analysis")

    report = ReportDraft(
        tenant_id=diagnosis_session.tenant_id,
        diagnosis_session_id=diagnosis_session.id,
        agent_run_id=agent_run.id,
        checklist_run_id=checklist_run.id,
        created_by_user_id=actor_user_id,
        title=_build_title(diagnosis_session),
        summary=_build_summary(diagnosis_session, agent_run, checklist_run),
        root_cause=_build_root_cause(agent_run),
        evidence_summary=_build_evidence_summary(agent_run),
        inspection_summary=_build_inspection_summary(checklist_run),
        recommended_action=_build_recommended_action(agent_run, checklist_run),
        safety_notes=_build_safety_notes(diagnosis_session, agent_run, checklist_run),
        status="DRAFT",
    )
    db.add(report)
    db.flush()
    create_audit_event(
        db,
        tenant_id=diagnosis_session.tenant_id,
        actor_user_id=actor_user_id,
        event_type="REPORT_DRAFT_CREATED",
        resource_type="report_draft",
        resource_id=report.id,
        severity="INFO",
        payload={
            "diagnosis_session_id": str(diagnosis_session.id),
            "agent_run_id": str(agent_run.id),
            "checklist_run_id": str(checklist_run.id),
        },
    )
    db.flush()
    return report


def submit_report_draft(
    db: Session,
    *,
    report_draft: ReportDraft,
    actor_user_id: uuid.UUID,
) -> None:
    if report_draft.status != "DRAFT":
        raise ReportPreconditionError("Only DRAFT reports can be submitted")
    report_draft.status = "SUBMITTED"
    create_audit_event(
        db,
        tenant_id=report_draft.tenant_id,
        actor_user_id=actor_user_id,
        event_type="REPORT_DRAFT_SUBMITTED",
        resource_type="report_draft",
        resource_id=report_draft.id,
        severity="INFO",
        payload={"previous_status": "DRAFT", "status": "SUBMITTED"},
    )
    db.flush()


def decide_report_draft(
    db: Session,
    *,
    report_draft: ReportDraft,
    actor_user_id: uuid.UUID,
    decision: str,
    comment: str | None,
) -> ReportApproval:
    if report_draft.status != "SUBMITTED":
        raise ReportPreconditionError("Only SUBMITTED reports can be approved or rejected")
    report_draft.status = decision
    approval = ReportApproval(
        tenant_id=report_draft.tenant_id,
        report_draft_id=report_draft.id,
        approver_user_id=actor_user_id,
        decision=decision,
        comment=comment,
    )
    db.add(approval)
    db.flush()
    create_audit_event(
        db,
        tenant_id=report_draft.tenant_id,
        actor_user_id=actor_user_id,
        event_type="REPORT_DRAFT_APPROVED" if decision == "APPROVED" else "REPORT_DRAFT_REJECTED",
        resource_type="report_draft",
        resource_id=report_draft.id,
        severity="INFO" if decision == "APPROVED" else "WARNING",
        payload={"decision": decision, "approval_id": str(approval.id), "comment": comment},
    )
    db.flush()
    return approval


def _latest_completed_agent_run(db: Session, diagnosis_session: DiagnosisSession) -> AgentRun | None:
    return db.scalar(
        select(AgentRun)
        .where(
            AgentRun.tenant_id == diagnosis_session.tenant_id,
            AgentRun.session_id == diagnosis_session.id,
            AgentRun.status == "COMPLETED",
        )
        .order_by(AgentRun.completed_at.desc(), AgentRun.started_at.desc())
        .limit(1)
    )


def _latest_valid_checklist_run(
    db: Session,
    diagnosis_session: DiagnosisSession,
    agent_run: AgentRun,
) -> ChecklistRun | None:
    return db.scalar(
        select(ChecklistRun)
        .where(
            ChecklistRun.tenant_id == diagnosis_session.tenant_id,
            ChecklistRun.diagnosis_session_id == diagnosis_session.id,
            ChecklistRun.agent_run_id == agent_run.id,
            ChecklistRun.status.in_(VALID_CHECKLIST_STATUSES),
        )
        .order_by(ChecklistRun.updated_at.desc(), ChecklistRun.created_at.desc())
        .limit(1)
    )


def _build_title(diagnosis_session: DiagnosisSession) -> str:
    equipment_code = diagnosis_session.equipment.code if diagnosis_session.equipment is not None else "UNKNOWN"
    return f"Diagnosis Report - {equipment_code} - {diagnosis_session.alarm_code}"


def _build_summary(
    diagnosis_session: DiagnosisSession,
    agent_run: AgentRun,
    checklist_run: ChecklistRun,
) -> str:
    return _join_lines(
        [
            f"Alarm: {diagnosis_session.alarm_code}",
            f"Symptom: {diagnosis_session.symptom_summary}",
            f"EtherCAT state: {diagnosis_session.ethercat_state or 'UNKNOWN'}",
            f"Diagnosis status: {diagnosis_session.status}",
            f"Agent run status: {agent_run.status}",
            f"Checklist run status: {checklist_run.status}",
        ]
    )


def _build_root_cause(agent_run: AgentRun) -> str:
    hypotheses = sorted(agent_run.hypotheses, key=lambda item: item.rank)
    if not hypotheses:
        return "No deterministic hypothesis was stored for this completed agent run."
    top = hypotheses[0]
    return _join_lines([f"Top hypothesis: {top.title}", f"Reasoning: {top.reasoning}", f"Confidence: {top.confidence_band}"])


def _build_evidence_summary(agent_run: AgentRun) -> str:
    rows: list[str] = []
    seen_codes: set[str] = set()
    for hypothesis in sorted(agent_run.hypotheses, key=lambda item: item.rank):
        for link in sorted(hypothesis.evidence_links, key=lambda item: item.source_code):
            if link.source_code in seen_codes:
                continue
            seen_codes.add(link.source_code)
            rows.append(f"{link.source_code}: {link.title} - {link.relevance_reason}")
    return _join_lines(rows or ["No evidence links were stored for this agent run."])


def _build_inspection_summary(checklist_run: ChecklistRun) -> str:
    rows = [
        f"{item.item_order}. {item.title} [{item.status}]"
        + (f" Note: {item.field_note}" if item.field_note else "")
        for item in sorted(checklist_run.items, key=lambda item: item.item_order)
    ]
    return _join_lines(rows or ["No checklist items were recorded."])


def _build_recommended_action(agent_run: AgentRun, checklist_run: ChecklistRun) -> str:
    checks: list[str] = []
    for hypothesis in sorted(agent_run.hypotheses, key=lambda item: item.rank):
        checks.extend(hypothesis.recommended_next_checks)
    checklist_actions = [
        f"Resolve blocked checklist item: {item.title}"
        for item in sorted(checklist_run.items, key=lambda item: item.item_order)
        if item.status == "BLOCKED"
    ]
    return _join_lines((checks + checklist_actions) or ["Continue read-only evidence collection before any action."])


def _build_safety_notes(
    diagnosis_session: DiagnosisSession,
    agent_run: AgentRun,
    checklist_run: ChecklistRun,
) -> str:
    blocked_count = sum(1 for item in checklist_run.items if item.status == "BLOCKED")
    return _join_lines(
        [
            f"Risk level: {diagnosis_session.risk_level}",
            f"Safety result: {agent_run.safety_result}",
            f"Blocked checklist items: {blocked_count}",
            "Do not defeat safety interlocks, command machine outputs, or issue machine-control commands from this report.",
            "Senior approval is required before risky recovery work.",
        ]
    )


def _join_lines(lines: list[str]) -> str:
    return "\n".join(lines)
