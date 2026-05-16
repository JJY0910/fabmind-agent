"""Create PR-23 read-only equipment data adapter tables.

Revision ID: 20260516_0006
Revises: 20260516_0005
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_0006"
down_revision = "20260516_0005"
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "equipment_alarm_events",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("diagnosis_session_id", UUID, sa.ForeignKey("diagnosis_sessions.id"), nullable=True),
        sa.Column("source_event_id", sa.String(length=160), nullable=True),
        sa.Column("alarm_code", sa.String(length=80), nullable=False),
        sa.Column("alarm_name", sa.String(length=240), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("event_status", sa.String(length=40), server_default="ACTIVE", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_equipment_alarm_events_severity",
        ),
        sa.CheckConstraint(
            "event_status IN ('ACTIVE','ACKNOWLEDGED','CLEARED')",
            name="ck_equipment_alarm_events_status",
        ),
    )
    op.create_index(
        "idx_equipment_alarm_events_tenant_occurred",
        "equipment_alarm_events",
        ["tenant_id", "occurred_at", "received_at"],
    )
    op.create_index("idx_equipment_alarm_events_equipment", "equipment_alarm_events", ["tenant_id", "equipment_id"])
    op.create_index("idx_equipment_alarm_events_severity", "equipment_alarm_events", ["tenant_id", "severity"])
    op.create_index("idx_equipment_alarm_events_status", "equipment_alarm_events", ["tenant_id", "event_status"])

    op.create_table(
        "equipment_io_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=160), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("observed_inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_outputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index(
        "idx_equipment_io_snapshots_tenant_captured",
        "equipment_io_snapshots",
        ["tenant_id", "captured_at", "received_at"],
    )
    op.create_index("idx_equipment_io_snapshots_equipment", "equipment_io_snapshots", ["tenant_id", "equipment_id"])

    op.create_table(
        "equipment_ethercat_status_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=160), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_system", sa.String(length=120), nullable=False),
        sa.Column("master_state", sa.String(length=40), nullable=False),
        sa.Column("slave_count", sa.Integer(), nullable=False),
        sa.Column("working_counter", sa.Integer(), nullable=True),
        sa.Column("link_status", sa.String(length=80), nullable=False),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index(
        "idx_equipment_ethercat_status_snapshots_tenant_captured",
        "equipment_ethercat_status_snapshots",
        ["tenant_id", "captured_at", "received_at"],
    )
    op.create_index(
        "idx_equipment_ethercat_status_snapshots_equipment",
        "equipment_ethercat_status_snapshots",
        ["tenant_id", "equipment_id"],
    )
    op.create_index(
        "idx_equipment_ethercat_status_snapshots_master_state",
        "equipment_ethercat_status_snapshots",
        ["tenant_id", "master_state"],
    )


def downgrade() -> None:
    op.drop_index("idx_equipment_ethercat_status_snapshots_master_state", table_name="equipment_ethercat_status_snapshots")
    op.drop_index("idx_equipment_ethercat_status_snapshots_equipment", table_name="equipment_ethercat_status_snapshots")
    op.drop_index("idx_equipment_ethercat_status_snapshots_tenant_captured", table_name="equipment_ethercat_status_snapshots")
    op.drop_table("equipment_ethercat_status_snapshots")
    op.drop_index("idx_equipment_io_snapshots_equipment", table_name="equipment_io_snapshots")
    op.drop_index("idx_equipment_io_snapshots_tenant_captured", table_name="equipment_io_snapshots")
    op.drop_table("equipment_io_snapshots")
    op.drop_index("idx_equipment_alarm_events_status", table_name="equipment_alarm_events")
    op.drop_index("idx_equipment_alarm_events_severity", table_name="equipment_alarm_events")
    op.drop_index("idx_equipment_alarm_events_equipment", table_name="equipment_alarm_events")
    op.drop_index("idx_equipment_alarm_events_tenant_occurred", table_name="equipment_alarm_events")
    op.drop_table("equipment_alarm_events")
