from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, ChecklistItem, ChecklistRun, DiagnosisSession, InspectionPlanItem
from app.services.audit import create_audit_event


TERMINAL_ITEM_STATUSES = {"DONE", "SKIPPED"}


class ChecklistRunPreconditionError(ValueError):
    pass


def create_checklist_run_from_latest_analysis(
    db: Session,
    *,
    diagnosis_session: DiagnosisSession,
    actor_user_id: uuid.UUID,
) -> ChecklistRun:
    agent_run = db.scalar(
        select(AgentRun)
        .where(
            AgentRun.tenant_id == diagnosis_session.tenant_id,
            AgentRun.session_id == diagnosis_session.id,
            AgentRun.status == "COMPLETED",
        )
        .order_by(AgentRun.completed_at.desc(), AgentRun.started_at.desc())
        .limit(1)
    )
    if agent_run is None:
        raise ChecklistRunPreconditionError("No completed agent analysis exists for this diagnosis session")

    inspection_items = db.scalars(
        select(InspectionPlanItem)
        .where(
            InspectionPlanItem.tenant_id == diagnosis_session.tenant_id,
            InspectionPlanItem.agent_run_id == agent_run.id,
        )
        .order_by(InspectionPlanItem.item_order)
    ).all()
    if not inspection_items:
        raise ChecklistRunPreconditionError("No inspection plan items exist for the latest completed agent analysis")

    checklist_run = ChecklistRun(
        tenant_id=diagnosis_session.tenant_id,
        diagnosis_session_id=diagnosis_session.id,
        agent_run_id=agent_run.id,
        created_by_user_id=actor_user_id,
        status="CREATED",
    )
    db.add(checklist_run)
    db.flush()

    for source in inspection_items:
        db.add(
            ChecklistItem(
                tenant_id=diagnosis_session.tenant_id,
                checklist_run_id=checklist_run.id,
                source_inspection_plan_item_id=source.id,
                item_order=source.item_order,
                title=source.title,
                description=source.instruction,
                expected_result=source.expected_observation,
                status="TODO",
            )
        )

    create_audit_event(
        db,
        tenant_id=diagnosis_session.tenant_id,
        actor_user_id=actor_user_id,
        event_type="CHECKLIST_RUN_CREATED",
        resource_type="checklist_run",
        resource_id=checklist_run.id,
        severity="INFO",
        payload={
            "diagnosis_session_id": str(diagnosis_session.id),
            "agent_run_id": str(agent_run.id),
            "item_count": len(inspection_items),
        },
    )
    db.flush()
    return checklist_run


def update_checklist_item(
    db: Session,
    *,
    checklist_run: ChecklistRun,
    item: ChecklistItem,
    actor_user_id: uuid.UUID,
    status: str | None,
    field_note: str | None,
) -> None:
    previous_status = item.status
    if status is not None:
        item.status = status
        if status in TERMINAL_ITEM_STATUSES:
            item.completed_by_user_id = actor_user_id
            item.completed_at = datetime.now(UTC)
        elif previous_status in TERMINAL_ITEM_STATUSES:
            item.completed_by_user_id = None
            item.completed_at = None

    if field_note is not None:
        item.field_note = field_note

    _recompute_run_status(checklist_run)
    create_audit_event(
        db,
        tenant_id=checklist_run.tenant_id,
        actor_user_id=actor_user_id,
        event_type="CHECKLIST_ITEM_STATUS_UPDATED",
        resource_type="checklist_item",
        resource_id=item.id,
        severity="INFO",
        payload={
            "checklist_run_id": str(checklist_run.id),
            "previous_status": previous_status,
            "status": item.status,
            "field_note_updated": field_note is not None,
        },
    )

    if status == "DONE":
        create_audit_event(
            db,
            tenant_id=checklist_run.tenant_id,
            actor_user_id=actor_user_id,
            event_type="CHECKLIST_ITEM_COMPLETED",
            resource_type="checklist_item",
            resource_id=item.id,
            severity="INFO",
            payload={"checklist_run_id": str(checklist_run.id), "item_order": item.item_order},
        )
    elif status == "BLOCKED":
        create_audit_event(
            db,
            tenant_id=checklist_run.tenant_id,
            actor_user_id=actor_user_id,
            event_type="CHECKLIST_ITEM_BLOCKED",
            resource_type="checklist_item",
            resource_id=item.id,
            severity="WARNING",
            payload={"checklist_run_id": str(checklist_run.id), "item_order": item.item_order},
        )
    db.flush()


def _recompute_run_status(checklist_run: ChecklistRun) -> None:
    item_statuses = [item.status for item in checklist_run.items]
    if any(status == "BLOCKED" for status in item_statuses):
        checklist_run.status = "BLOCKED"
    elif item_statuses and all(status in TERMINAL_ITEM_STATUSES for status in item_statuses):
        checklist_run.status = "COMPLETED"
    elif any(status == "IN_PROGRESS" for status in item_statuses) or any(status in TERMINAL_ITEM_STATUSES for status in item_statuses):
        checklist_run.status = "IN_PROGRESS"
    else:
        checklist_run.status = "CREATED"
