from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import (
    AgentRun,
    ChecklistItem,
    ChecklistRun,
    DiagnosisHypothesis,
    DiagnosisSession,
    EvidenceLink,
    ReportDraft,
    User,
)
from app.schemas import DashboardRecentDiagnosisSession, DashboardRequiredAction, DashboardSummaryResponse


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
ACTIVE_DIAGNOSIS_STATUSES = ("CREATED", "ANALYZING", "ANALYSIS_READY", "INSUFFICIENT_EVIDENCE")
OPEN_CHECKLIST_STATUSES = ("CREATED", "IN_PROGRESS", "BLOCKED")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    tenant_id = current_user.tenant_id
    active_diagnosis_count = _scalar_count(
        db,
        select(func.count())
        .select_from(DiagnosisSession)
        .where(DiagnosisSession.tenant_id == tenant_id, DiagnosisSession.status.in_(ACTIVE_DIAGNOSIS_STATUSES)),
    )
    pending_approval_count = _scalar_count(
        db,
        select(func.count())
        .select_from(ReportDraft)
        .where(ReportDraft.tenant_id == tenant_id, ReportDraft.status == "SUBMITTED"),
    )
    high_risk_count = _scalar_count(
        db,
        select(func.count())
        .select_from(DiagnosisSession)
        .where(
            DiagnosisSession.tenant_id == tenant_id,
            DiagnosisSession.status.in_(ACTIVE_DIAGNOSIS_STATUSES),
            DiagnosisSession.risk_level.in_(("HIGH", "CRITICAL")),
        ),
    )
    open_checklist_count = _scalar_count(
        db,
        select(func.count())
        .select_from(ChecklistRun)
        .where(ChecklistRun.tenant_id == tenant_id, ChecklistRun.status.in_(OPEN_CHECKLIST_STATUSES)),
    )
    submitted_report_count = pending_approval_count
    approved_report_count = _scalar_count(
        db,
        select(func.count())
        .select_from(ReportDraft)
        .where(ReportDraft.tenant_id == tenant_id, ReportDraft.status == "APPROVED"),
    )
    guardrail_blocks_today = _scalar_count(
        db,
        select(func.count())
        .select_from(AgentRun)
        .where(
            AgentRun.tenant_id == tenant_id,
            AgentRun.status == "SAFETY_BLOCKED",
            AgentRun.started_at >= _today_start(),
        ),
    )

    return DashboardSummaryResponse(
        active_diagnosis_count=active_diagnosis_count,
        pending_approval_count=pending_approval_count,
        high_risk_count=high_risk_count,
        evidence_linked_rate=_evidence_linked_rate(db, tenant_id),
        open_checklist_count=open_checklist_count,
        submitted_report_count=submitted_report_count,
        approved_report_count=approved_report_count,
        recent_diagnosis_sessions=_recent_diagnosis_sessions(db, tenant_id),
        required_actions=_required_actions(db, tenant_id),
        guardrail_blocks_today=guardrail_blocks_today,
    )


def _scalar_count(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


def _today_start() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _evidence_linked_rate(db: Session, tenant_id) -> float:
    total_hypotheses = _scalar_count(
        db,
        select(func.count()).select_from(DiagnosisHypothesis).where(DiagnosisHypothesis.tenant_id == tenant_id),
    )
    if total_hypotheses == 0:
        return 0.0

    linked_hypotheses = _scalar_count(
        db,
        select(func.count(func.distinct(EvidenceLink.hypothesis_id)))
        .select_from(EvidenceLink)
        .join(DiagnosisHypothesis, EvidenceLink.hypothesis_id == DiagnosisHypothesis.id)
        .where(DiagnosisHypothesis.tenant_id == tenant_id, EvidenceLink.hypothesis_id.is_not(None)),
    )
    return round(linked_hypotheses / total_hypotheses, 2)


def _recent_diagnosis_sessions(db: Session, tenant_id) -> list[DashboardRecentDiagnosisSession]:
    sessions = db.scalars(
        select(DiagnosisSession)
        .options(joinedload(DiagnosisSession.equipment))
        .where(DiagnosisSession.tenant_id == tenant_id)
        .order_by(DiagnosisSession.created_at.desc())
        .limit(5)
    ).all()
    return [
        DashboardRecentDiagnosisSession(
            session_id=session.id,
            equipment_code=session.equipment.code,
            alarm_code=session.alarm_code,
            status=session.status,
            risk_level=session.risk_level,
            created_at=session.created_at,
        )
        for session in sessions
    ]


def _required_actions(db: Session, tenant_id) -> list[DashboardRequiredAction]:
    actions: list[DashboardRequiredAction] = []
    actions.extend(_report_approval_actions(db, tenant_id))
    actions.extend(_blocked_checklist_actions(db, tenant_id))
    actions.extend(_high_risk_diagnosis_actions(db, tenant_id))
    actions.extend(_safety_blocked_run_actions(db, tenant_id))
    return sorted(actions, key=lambda item: item.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:20]


def _report_approval_actions(db: Session, tenant_id) -> list[DashboardRequiredAction]:
    reports = db.scalars(
        select(ReportDraft)
        .where(ReportDraft.tenant_id == tenant_id, ReportDraft.status == "SUBMITTED")
        .order_by(ReportDraft.updated_at.desc())
        .limit(10)
    ).all()
    return [
        DashboardRequiredAction(
            action_type="REPORT_APPROVAL",
            resource_type="report_draft",
            resource_id=report.id,
            title=f"Review submitted report: {report.title}",
            severity="APPROVAL",
            created_at=report.updated_at,
        )
        for report in reports
    ]


def _blocked_checklist_actions(db: Session, tenant_id) -> list[DashboardRequiredAction]:
    items = db.scalars(
        select(ChecklistItem)
        .join(ChecklistRun, ChecklistItem.checklist_run_id == ChecklistRun.id)
        .where(
            ChecklistItem.tenant_id == tenant_id,
            ChecklistRun.tenant_id == tenant_id,
            ChecklistItem.status == "BLOCKED",
        )
        .order_by(ChecklistItem.updated_at.desc())
        .limit(10)
    ).all()
    return [
        DashboardRequiredAction(
            action_type="BLOCKED_CHECKLIST_ITEM",
            resource_type="checklist_item",
            resource_id=item.id,
            title=f"Resolve blocked checklist item: {item.title}",
            severity="WARNING",
            created_at=item.updated_at,
        )
        for item in items
    ]


def _high_risk_diagnosis_actions(db: Session, tenant_id) -> list[DashboardRequiredAction]:
    sessions = db.scalars(
        select(DiagnosisSession)
        .where(
            DiagnosisSession.tenant_id == tenant_id,
            DiagnosisSession.status.in_(ACTIVE_DIAGNOSIS_STATUSES),
            DiagnosisSession.risk_level.in_(("HIGH", "CRITICAL")),
        )
        .order_by(DiagnosisSession.created_at.desc())
        .limit(10)
    ).all()
    return [
        DashboardRequiredAction(
            action_type="HIGH_RISK_DIAGNOSIS",
            resource_type="diagnosis_session",
            resource_id=session.id,
            title=f"Review high-risk diagnosis: {session.alarm_code}",
            severity=session.risk_level,
            created_at=session.created_at,
        )
        for session in sessions
    ]


def _safety_blocked_run_actions(db: Session, tenant_id) -> list[DashboardRequiredAction]:
    runs = db.scalars(
        select(AgentRun)
        .where(AgentRun.tenant_id == tenant_id, AgentRun.status == "SAFETY_BLOCKED")
        .order_by(AgentRun.started_at.desc())
        .limit(10)
    ).all()
    return [
        DashboardRequiredAction(
            action_type="SAFETY_BLOCKED_AGENT_RUN",
            resource_type="agent_run",
            resource_id=run.id,
            title="Review safety guardrail blocked analysis",
            severity="CRITICAL",
            created_at=run.started_at,
        )
        for run in runs
    ]
