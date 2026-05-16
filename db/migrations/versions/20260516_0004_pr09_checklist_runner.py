"""Create PR-09 checklist runner tables.

Revision ID: 20260516_0004
Revises: 20260515_0003
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_0004"
down_revision = "20260515_0003"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "checklist_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("diagnosis_session_id", UUID, sa.ForeignKey("diagnosis_sessions.id"), nullable=False),
        sa.Column("agent_run_id", UUID, sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("created_by_user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="CREATED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('CREATED','IN_PROGRESS','COMPLETED','BLOCKED')",
            name="ck_checklist_runs_status",
        ),
    )
    op.create_index("idx_checklist_runs_tenant_session", "checklist_runs", ["tenant_id", "diagnosis_session_id"])
    op.create_index("idx_checklist_runs_agent_run", "checklist_runs", ["tenant_id", "agent_run_id"])
    op.create_table(
        "checklist_items",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("checklist_run_id", UUID, sa.ForeignKey("checklist_runs.id"), nullable=False),
        sa.Column("source_inspection_plan_item_id", UUID, sa.ForeignKey("inspection_plan_items.id"), nullable=False),
        sa.Column("item_order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="TODO", nullable=False),
        sa.Column("field_note", sa.Text(), nullable=True),
        sa.Column("completed_by_user_id", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('TODO','IN_PROGRESS','DONE','BLOCKED','SKIPPED')",
            name="ck_checklist_items_status",
        ),
        sa.UniqueConstraint("checklist_run_id", "item_order", name="uq_checklist_items_run_order"),
    )
    op.create_index("idx_checklist_items_run", "checklist_items", ["checklist_run_id"])


def downgrade() -> None:
    op.drop_index("idx_checklist_items_run", table_name="checklist_items")
    op.drop_table("checklist_items")
    op.drop_index("idx_checklist_runs_agent_run", table_name="checklist_runs")
    op.drop_index("idx_checklist_runs_tenant_session", table_name="checklist_runs")
    op.drop_table("checklist_runs")
