"""Create PR-02 domain foundation tables.

Revision ID: 20260515_0001
Revises:
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0001"
down_revision = None
branch_labels = None
depends_on = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_tenants_code"),
    )
    op.create_table(
        "roles",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("role_id", UUID, sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
    )
    op.create_table(
        "sites",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sites_tenant_code"),
    )
    op.create_table(
        "lines",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("site_id", UUID, sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_lines_tenant_code"),
    )
    op.create_table(
        "equipment_families",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_equipment_families_tenant_code"),
    )
    op.create_table(
        "equipment",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("line_id", UUID, sa.ForeignKey("lines.id"), nullable=False),
        sa.Column("family_id", UUID, sa.ForeignKey("equipment_families.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("vendor", sa.String(length=120), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("revision", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="NORMAL", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_equipment_tenant_code"),
    )
    op.create_index("idx_equipment_tenant_id", "equipment", ["tenant_id"])
    op.create_table(
        "alarm_codes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_family_id", UUID, sa.ForeignKey("equipment_families.id"), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("primary_signal", sa.String(length=120), nullable=True),
        sa.Column("recommended_first_check", sa.Text(), nullable=True),
        sa.CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_alarm_codes_severity"),
        sa.UniqueConstraint("tenant_id", "equipment_family_id", "code", name="uq_alarm_codes_tenant_family_code"),
    )
    op.create_index("idx_alarm_codes_tenant_family", "alarm_codes", ["tenant_id", "equipment_family_id"])
    op.create_table(
        "io_points",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("signal_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("normal_state", sa.Boolean(), nullable=True),
        sa.Column("related_alarm_code", sa.String(length=80), nullable=True),
        sa.CheckConstraint("direction IN ('DI','DO')", name="ck_io_points_direction"),
        sa.UniqueConstraint("tenant_id", "equipment_id", "code", name="uq_io_points_tenant_equipment_code"),
    )
    op.create_index("idx_io_points_equipment", "io_points", ["tenant_id", "equipment_id"])
    op.create_table(
        "ethercat_devices",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("equipment_id", UUID, sa.ForeignKey("equipment.id"), nullable=False),
        sa.Column("slave_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("expected_state", sa.String(length=20), nullable=False),
        sa.Column("vendor_id", sa.String(length=80), nullable=True),
        sa.Column("product_code", sa.String(length=80), nullable=True),
        sa.CheckConstraint("expected_state IN ('INIT','PRE_OP','SAFE_OP','OP')", name="ck_ethercat_devices_expected_state"),
        sa.UniqueConstraint("tenant_id", "equipment_id", "slave_no", name="uq_ethercat_devices_tenant_equipment_slave"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_user_id", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", UUID, nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("severity IN ('INFO','WARNING','ERROR','SECURITY')", name="ck_audit_events_severity"),
    )
    op.create_index("idx_audit_events_tenant_created", "audit_events", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_events_tenant_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("ethercat_devices")
    op.drop_index("idx_io_points_equipment", table_name="io_points")
    op.drop_table("io_points")
    op.drop_index("idx_alarm_codes_tenant_family", table_name="alarm_codes")
    op.drop_table("alarm_codes")
    op.drop_index("idx_equipment_tenant_id", table_name="equipment")
    op.drop_table("equipment")
    op.drop_table("equipment_families")
    op.drop_table("lines")
    op.drop_table("sites")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("tenants")

