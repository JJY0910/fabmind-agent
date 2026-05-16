"""Create PR-10 report draft and approval tables.

Revision ID: 20260516_0005
Revises: 20260516_0004
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_0005"
down_revision = "20260516_0004"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "report_drafts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("diagnosis_session_id", UUID, sa.ForeignKey("diagnosis_sessions.id"), nullable=False),
        sa.Column("agent_run_id", UUID, sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("checklist_run_id", UUID, sa.ForeignKey("checklist_runs.id"), nullable=False),
        sa.Column("created_by_user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("inspection_summary", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("safety_notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT','SUBMITTED','APPROVED','REJECTED')",
            name="ck_report_drafts_status",
        ),
    )
    op.create_index("idx_report_drafts_tenant_session", "report_drafts", ["tenant_id", "diagnosis_session_id"])
    op.create_index("idx_report_drafts_tenant_status", "report_drafts", ["tenant_id", "status"])
    op.create_table(
        "report_approvals",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("report_draft_id", UUID, sa.ForeignKey("report_drafts.id"), nullable=False),
        sa.Column("approver_user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED')", name="ck_report_approvals_decision"),
    )
    op.create_index("idx_report_approvals_report", "report_approvals", ["tenant_id", "report_draft_id"])


def downgrade() -> None:
    op.drop_index("idx_report_approvals_report", table_name="report_approvals")
    op.drop_table("report_approvals")
    op.drop_index("idx_report_drafts_tenant_status", table_name="report_drafts")
    op.drop_index("idx_report_drafts_tenant_session", table_name="report_drafts")
    op.drop_table("report_drafts")
