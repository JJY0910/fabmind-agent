"""Add PR-25 operational query indexes.

Revision ID: 20260517_0008
Revises: 20260517_0007
Create Date: 2026-05-17
"""

from __future__ import annotations

from alembic import op

revision = "20260517_0008"
down_revision = "20260517_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_checklist_runs_tenant_status_updated",
        "checklist_runs",
        ["tenant_id", "status", "updated_at"],
    )
    op.create_index(
        "idx_report_drafts_tenant_status_updated",
        "report_drafts",
        ["tenant_id", "status", "updated_at"],
    )
    op.create_index(
        "idx_equipment_incidents_tenant_updated_opened",
        "equipment_incidents",
        ["tenant_id", "updated_at", "opened_at"],
    )
    op.create_index(
        "idx_equipment_incidents_severity",
        "equipment_incidents",
        ["tenant_id", "severity"],
    )
    op.create_index(
        "idx_audit_events_tenant_event_type_created",
        "audit_events",
        ["tenant_id", "event_type", "created_at"],
    )
    op.create_index(
        "idx_audit_events_tenant_severity_created",
        "audit_events",
        ["tenant_id", "severity", "created_at"],
    )
    op.create_index(
        "idx_audit_events_tenant_resource_created",
        "audit_events",
        ["tenant_id", "resource_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_audit_events_tenant_resource_created", table_name="audit_events")
    op.drop_index("idx_audit_events_tenant_severity_created", table_name="audit_events")
    op.drop_index("idx_audit_events_tenant_event_type_created", table_name="audit_events")
    op.drop_index("idx_equipment_incidents_severity", table_name="equipment_incidents")
    op.drop_index("idx_equipment_incidents_tenant_updated_opened", table_name="equipment_incidents")
    op.drop_index("idx_report_drafts_tenant_status_updated", table_name="report_drafts")
    op.drop_index("idx_checklist_runs_tenant_status_updated", table_name="checklist_runs")
