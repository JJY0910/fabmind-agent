from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import ReportApproval, ReportDraft, User
from app.schemas import ApprovalQueueItem, ApprovalQueueResponse


APPROVAL_ROLES = (ROLE_SENIOR, ROLE_ADMIN)
REVIEWABLE_REPORT_STATUSES = ("SUBMITTED", "APPROVED", "REJECTED")

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=ApprovalQueueResponse)
def list_approval_queue(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*APPROVAL_ROLES)),
    db: Session = Depends(get_db),
) -> ApprovalQueueResponse:
    filters = [ReportDraft.tenant_id == current_user.tenant_id]
    if status_filter == "PENDING_REVIEW":
        filters.append(ReportDraft.status == "SUBMITTED")
    elif status_filter in {"SUBMITTED", "APPROVED", "REJECTED"}:
        filters.append(ReportDraft.status == status_filter)
    else:
        filters.append(ReportDraft.status.in_(REVIEWABLE_REPORT_STATUSES))

    total = db.scalar(select(func.count()).select_from(ReportDraft).where(*filters)) or 0
    reports = (
        db.execute(
            select(ReportDraft)
            .options(
                joinedload(ReportDraft.created_by),
                joinedload(ReportDraft.approvals).joinedload(ReportApproval.approver).joinedload(User.role),
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
    return ApprovalQueueResponse(
        items=[_approval_queue_item(report) for report in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


def _approval_queue_item(report: ReportDraft) -> ApprovalQueueItem:
    latest_approval = _latest_approval(report.approvals)
    approval_status = "PENDING_REVIEW" if report.status == "SUBMITTED" else report.status
    reviewer_comment = latest_approval.comment if latest_approval is not None else None
    rejection_reason = reviewer_comment if latest_approval is not None and latest_approval.decision == "REJECTED" else None
    return ApprovalQueueItem(
        approval_id=latest_approval.id if latest_approval is not None else None,
        report_draft_id=report.id,
        approval_status=approval_status,
        requested_by=report.created_by.display_name,
        reviewer_id=latest_approval.approver_user_id if latest_approval is not None else None,
        reviewer_role=latest_approval.approver.role.code if latest_approval is not None else "SENIOR_ENGINEER_OR_ADMIN",
        requested_at=report.updated_at if report.status == "SUBMITTED" else report.created_at,
        reviewed_at=latest_approval.decided_at if latest_approval is not None else None,
        reviewer_comment=reviewer_comment,
        rejection_reason=rejection_reason,
    )


def _latest_approval(approvals: list[ReportApproval]) -> ReportApproval | None:
    if not approvals:
        return None
    return sorted(approvals, key=lambda item: item.decided_at, reverse=True)[0]
