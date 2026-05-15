from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    sites: Mapped[list["Site"]] = relationship(back_populates="tenant")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="tenant")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("roles.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    role: Mapped[Role] = relationship(back_populates="users")


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_sites_tenant_code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="sites")
    lines: Mapped[list["Line"]] = relationship(back_populates="site")


class Line(Base):
    __tablename__ = "lines"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lines_tenant_code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("sites.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    site: Mapped[Site] = relationship(back_populates="lines")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="line")


class EquipmentFamily(Base):
    __tablename__ = "equipment_families"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_equipment_families_tenant_code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    equipment: Mapped[list["Equipment"]] = relationship(back_populates="family")
    alarm_codes: Mapped[list["AlarmCode"]] = relationship(back_populates="equipment_family")


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_equipment_tenant_code"),
        Index("idx_equipment_tenant_id", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    line_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("lines.id"), nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment_families.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    revision: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="NORMAL", server_default="NORMAL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant: Mapped[Tenant] = relationship(back_populates="equipment")
    line: Mapped[Line] = relationship(back_populates="equipment")
    family: Mapped[EquipmentFamily] = relationship(back_populates="equipment")
    io_points: Mapped[list["IoPoint"]] = relationship(back_populates="equipment")
    ethercat_devices: Mapped[list["EthercatDevice"]] = relationship(back_populates="equipment")
    diagnosis_sessions: Mapped[list["DiagnosisSession"]] = relationship(back_populates="equipment")


class AlarmCode(Base):
    __tablename__ = "alarm_codes"
    __table_args__ = (
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_alarm_codes_severity"),
        UniqueConstraint("tenant_id", "equipment_family_id", "code", name="uq_alarm_codes_tenant_family_code"),
        Index("idx_alarm_codes_tenant_family", "tenant_id", "equipment_family_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_family_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment_families.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    primary_signal: Mapped[str | None] = mapped_column(String(120))
    recommended_first_check: Mapped[str | None] = mapped_column(Text)

    equipment_family: Mapped[EquipmentFamily] = relationship(back_populates="alarm_codes")


class IoPoint(Base):
    __tablename__ = "io_points"
    __table_args__ = (
        CheckConstraint("direction IN ('DI','DO')", name="ck_io_points_direction"),
        UniqueConstraint("tenant_id", "equipment_id", "code", name="uq_io_points_tenant_equipment_code"),
        Index("idx_io_points_equipment", "tenant_id", "equipment_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    normal_state: Mapped[bool | None] = mapped_column(Boolean)
    related_alarm_code: Mapped[str | None] = mapped_column(String(80))

    equipment: Mapped[Equipment] = relationship(back_populates="io_points")


class EthercatDevice(Base):
    __tablename__ = "ethercat_devices"
    __table_args__ = (
        CheckConstraint("expected_state IN ('INIT','PRE_OP','SAFE_OP','OP')", name="ck_ethercat_devices_expected_state"),
        UniqueConstraint("tenant_id", "equipment_id", "slave_no", name="uq_ethercat_devices_tenant_equipment_slave"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    slave_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_state: Mapped[str] = mapped_column(String(20), nullable=False)
    vendor_id: Mapped[str | None] = mapped_column(String(80))
    product_code: Mapped[str | None] = mapped_column(String(80))

    equipment: Mapped[Equipment] = relationship(back_populates="ethercat_devices")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint("severity IN ('INFO','WARNING','ERROR','SECURITY')", name="ck_audit_events_severity"),
        Index("idx_audit_events_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DiagnosisSession(Base):
    __tablename__ = "diagnosis_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED','ANALYZING','ANALYSIS_READY','INSUFFICIENT_EVIDENCE','CLOSED')",
            name="ck_diagnosis_sessions_status",
        ),
        CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_diagnosis_sessions_risk_level"),
        Index("idx_diagnosis_sessions_tenant_equipment", "tenant_id", "equipment_id"),
        Index("idx_diagnosis_sessions_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    alarm_code: Mapped[str] = mapped_column(String(80), nullable=False)
    symptom_summary: Mapped[str] = mapped_column(Text, nullable=False)
    log_excerpt: Mapped[str | None] = mapped_column(Text)
    ethercat_state: Mapped[str | None] = mapped_column(String(20))
    io_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    recent_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="CREATED", server_default="CREATED")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW", server_default="LOW")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment: Mapped[Equipment] = relationship(back_populates="diagnosis_sessions")
    created_by: Mapped[User] = relationship()
