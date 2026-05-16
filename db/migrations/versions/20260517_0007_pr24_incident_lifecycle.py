"""Create PR-24 incident lifecycle table.

Revision ID: 20260517_0007
Revises: 20260516_0006
Create Date: 2026-05-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260517_0007"
down_revision = "20260516_0006"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "equipment_incidents",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("primary_alarm_event_id", UUID, sa.ForeignKey("equipment_alarm_events.id"), nullable=True),
        sa.Column("diagnosis_session_id", UUID, sa.ForeignKey("diagnosis_sessions.id"), nullable=True),
        sa.Column("checklist_run_id", UUID, sa.ForeignKey("checklist_runs.id"), nullable=True),
        sa.Column("report_draft_id", UUID, sa.ForeignKey("report_drafts.id"), nullable=True),
        sa.Column("approval_id", UUID, sa.ForeignKey("report_approvals.id"), nullable=True),
        sa.Column("case_number", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("alarm_code", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="OPEN", nullable=False),
        sa.Column("owner_user_id", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_role", sa.String(length=80), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checklist_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('OPEN','TRIAGED','CHECKLIST_IN_PROGRESS','REPORT_SUBMITTED','APPROVED','CLOSED','CANCELLED')",
            name="ck_equipment_incidents_status",
        ),
        sa.CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_equipment_incidents_severity",
        ),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_equipment_incidents_tenant_case_number"),
    )
    op.create_index(
        "idx_equipment_incidents_tenant_status_updated",
        "equipment_incidents",
        ["tenant_id", "status", "updated_at"],
    )
    op.create_index("idx_equipment_incidents_equipment", "equipment_incidents", ["tenant_id", "equipment_id"])
    op.create_index("idx_equipment_incidents_alarm_code", "equipment_incidents", ["tenant_id", "alarm_code"])
    op.create_index(
        "idx_equipment_incidents_primary_alarm",
        "equipment_incidents",
        ["tenant_id", "primary_alarm_event_id"],
    )

    op.execute(
        """
        INSERT INTO equipment_incidents (
            id,
            tenant_id,
            equipment_id,
            diagnosis_session_id,
            case_number,
            title,
            summary,
            alarm_code,
            severity,
            status,
            owner_user_id,
            assigned_role,
            opened_at,
            closed_at,
            created_at,
            updated_at
        )
        SELECT
            ds.id,
            ds.tenant_id,
            ds.equipment_id,
            ds.id,
            'INC-' || e.code || '-' || substring(replace(ds.id::text, '-', '') from 1 for 10),
            e.code || ' ' || ds.alarm_code,
            ds.symptom_summary,
            ds.alarm_code,
            ds.risk_level,
            CASE WHEN ds.status = 'CLOSED' THEN 'CLOSED' ELSE 'OPEN' END,
            ds.created_by_user_id,
            'FIELD_ENGINEER',
            ds.created_at,
            CASE WHEN ds.status = 'CLOSED' THEN ds.updated_at ELSE NULL END,
            ds.created_at,
            ds.updated_at
        FROM diagnosis_sessions ds
        JOIN equipment e ON e.id = ds.equipment_id
        WHERE NOT EXISTS (
            SELECT 1 FROM equipment_incidents existing
            WHERE existing.tenant_id = ds.tenant_id
              AND existing.diagnosis_session_id = ds.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index("idx_equipment_incidents_primary_alarm", table_name="equipment_incidents")
    op.drop_index("idx_equipment_incidents_alarm_code", table_name="equipment_incidents")
    op.drop_index("idx_equipment_incidents_equipment", table_name="equipment_incidents")
    op.drop_index("idx_equipment_incidents_tenant_status_updated", table_name="equipment_incidents")
    op.drop_table("equipment_incidents")
