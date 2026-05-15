"""Create PR-06 diagnosis session table.

Revision ID: 20260515_0002
Revises: 20260515_0001
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0002"
down_revision = "20260515_0001"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "diagnosis_sessions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("created_by_user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("alarm_code", sa.String(length=80), nullable=False),
        sa.Column("symptom_summary", sa.Text(), nullable=False),
        sa.Column("log_excerpt", sa.Text(), nullable=True),
        sa.Column("ethercat_state", sa.String(length=20), nullable=True),
        sa.Column("io_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recent_action", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="CREATED", nullable=False),
        sa.Column("risk_level", sa.String(length=20), server_default="LOW", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('CREATED','ANALYZING','ANALYSIS_READY','INSUFFICIENT_EVIDENCE','CLOSED')",
            name="ck_diagnosis_sessions_status",
        ),
        sa.CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_diagnosis_sessions_risk_level"),
    )
    op.create_index("idx_diagnosis_sessions_tenant_equipment", "diagnosis_sessions", ["tenant_id", "equipment_id"])
    op.create_index("idx_diagnosis_sessions_tenant_created", "diagnosis_sessions", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_diagnosis_sessions_tenant_created", table_name="diagnosis_sessions")
    op.drop_index("idx_diagnosis_sessions_tenant_equipment", table_name="diagnosis_sessions")
    op.drop_table("diagnosis_sessions")

