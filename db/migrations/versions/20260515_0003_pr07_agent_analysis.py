"""Create PR-07 deterministic agent analysis tables.

Revision ID: 20260515_0003
Revises: 20260515_0002
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0003"
down_revision = "20260515_0002"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("session_id", UUID, sa.ForeignKey("diagnosis_sessions.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("mode", sa.String(length=40), server_default="DETERMINISTIC", nullable=False),
        sa.Column("safety_result", sa.String(length=80), server_default="SAFE_READ_ONLY", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('COMPLETED','INSUFFICIENT_EVIDENCE','SAFETY_BLOCKED','FAILED')",
            name="ck_agent_runs_status",
        ),
    )
    op.create_index("idx_agent_runs_session", "agent_runs", ["tenant_id", "session_id"])
    op.create_table(
        "agent_steps",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_run_id", UUID, sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_run_id", "step_order", name="uq_agent_steps_run_order"),
    )
    op.create_index("idx_agent_steps_run", "agent_steps", ["agent_run_id"])
    op.create_table(
        "diagnosis_hypotheses",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_run_id", UUID, sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("confidence_band", sa.String(length=20), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("recommended_next_checks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("confidence_band IN ('HIGH','MEDIUM','LOW')", name="ck_diagnosis_hypotheses_confidence_band"),
        sa.CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_diagnosis_hypotheses_risk_level"),
        sa.UniqueConstraint("agent_run_id", "rank", name="uq_diagnosis_hypotheses_run_rank"),
    )
    op.create_table(
        "evidence_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("hypothesis_id", UUID, sa.ForeignKey("diagnosis_hypotheses.id"), nullable=True),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_code", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("relevance_reason", sa.Text(), nullable=False),
    )
    op.create_index("idx_evidence_links_hypothesis", "evidence_links", ["hypothesis_id"])
    op.create_table(
        "inspection_plan_items",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("agent_run_id", UUID, sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("item_order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("expected_observation", sa.Text(), nullable=True),
        sa.Column("safety_level", sa.String(length=40), server_default="NORMAL", nullable=False),
        sa.Column("evidence_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "safety_level IN ('NORMAL','CAUTION','APPROVAL_REQUIRED')",
            name="ck_inspection_plan_items_safety_level",
        ),
        sa.UniqueConstraint("agent_run_id", "item_order", name="uq_inspection_plan_items_run_order"),
    )


def downgrade() -> None:
    op.drop_table("inspection_plan_items")
    op.drop_index("idx_evidence_links_hypothesis", table_name="evidence_links")
    op.drop_table("evidence_links")
    op.drop_table("diagnosis_hypotheses")
    op.drop_index("idx_agent_steps_run", table_name="agent_steps")
    op.drop_table("agent_steps")
    op.drop_index("idx_agent_runs_session", table_name="agent_runs")
    op.drop_table("agent_runs")

