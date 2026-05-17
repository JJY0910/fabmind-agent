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
    alarm_events: Mapped[list["EquipmentAlarmEvent"]] = relationship(back_populates="equipment")
    io_snapshots: Mapped[list["EquipmentIOSnapshot"]] = relationship(back_populates="equipment")
    ethercat_status_snapshots: Mapped[list["EquipmentEthercatStatusSnapshot"]] = relationship(back_populates="equipment")
    incidents: Mapped[list["EquipmentIncident"]] = relationship(back_populates="equipment")


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


class EquipmentAlarmEvent(Base):
    __tablename__ = "equipment_alarm_events"
    __table_args__ = (
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_equipment_alarm_events_severity"),
        CheckConstraint(
            "event_status IN ('ACTIVE','ACKNOWLEDGED','CLEARED')",
            name="ck_equipment_alarm_events_status",
        ),
        Index("idx_equipment_alarm_events_tenant_occurred", "tenant_id", "occurred_at", "received_at"),
        Index("idx_equipment_alarm_events_equipment", "tenant_id", "equipment_id"),
        Index("idx_equipment_alarm_events_severity", "tenant_id", "severity"),
        Index("idx_equipment_alarm_events_status", "tenant_id", "event_status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    diagnosis_session_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("diagnosis_sessions.id"))
    source_event_id: Mapped[str | None] = mapped_column(String(160))
    alarm_code: Mapped[str] = mapped_column(String(80), nullable=False)
    alarm_name: Mapped[str | None] = mapped_column(String(240))
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    event_status: Mapped[str] = mapped_column(String(40), nullable=False, default="ACTIVE", server_default="ACTIVE")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    equipment: Mapped[Equipment] = relationship(back_populates="alarm_events")
    diagnosis_session: Mapped[DiagnosisSession | None] = relationship()


class EquipmentIOSnapshot(Base):
    __tablename__ = "equipment_io_snapshots"
    __table_args__ = (
        Index("idx_equipment_io_snapshots_tenant_captured", "tenant_id", "captured_at", "received_at"),
        Index("idx_equipment_io_snapshots_equipment", "tenant_id", "equipment_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(160))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    observed_inputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    observed_outputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    equipment: Mapped[Equipment] = relationship(back_populates="io_snapshots")


class EquipmentEthercatStatusSnapshot(Base):
    __tablename__ = "equipment_ethercat_status_snapshots"
    __table_args__ = (
        Index(
            "idx_equipment_ethercat_status_snapshots_tenant_captured",
            "tenant_id",
            "captured_at",
            "received_at",
        ),
        Index("idx_equipment_ethercat_status_snapshots_equipment", "tenant_id", "equipment_id"),
        Index("idx_equipment_ethercat_status_snapshots_master_state", "tenant_id", "master_state"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(160))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    master_state: Mapped[str] = mapped_column(String(40), nullable=False)
    slave_count: Mapped[int] = mapped_column(Integer, nullable=False)
    working_counter: Mapped[int | None] = mapped_column(Integer)
    link_status: Mapped[str] = mapped_column(String(80), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(120))
    error_summary: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    equipment: Mapped[Equipment] = relationship(back_populates="ethercat_status_snapshots")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint("severity IN ('INFO','WARNING','ERROR','SECURITY')", name="ck_audit_events_severity"),
        Index("idx_audit_events_tenant_created", "tenant_id", "created_at"),
        Index("idx_audit_events_tenant_event_type_created", "tenant_id", "event_type", "created_at"),
        Index("idx_audit_events_tenant_severity_created", "tenant_id", "severity", "created_at"),
        Index("idx_audit_events_tenant_resource_created", "tenant_id", "resource_type", "created_at"),
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
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="session")
    checklist_runs: Mapped[list["ChecklistRun"]] = relationship(back_populates="diagnosis_session")
    report_drafts: Mapped[list["ReportDraft"]] = relationship(back_populates="diagnosis_session")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('COMPLETED','INSUFFICIENT_EVIDENCE','SAFETY_BLOCKED','FAILED')",
            name="ck_agent_runs_status",
        ),
        Index("idx_agent_runs_session", "tenant_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("diagnosis_sessions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    mode: Mapped[str] = mapped_column(String(40), nullable=False, default="DETERMINISTIC", server_default="DETERMINISTIC")
    safety_result: Mapped[str] = mapped_column(String(80), nullable=False, default="SAFE_READ_ONLY", server_default="SAFE_READ_ONLY")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[DiagnosisSession] = relationship(back_populates="agent_runs")
    steps: Mapped[list["AgentStep"]] = relationship(back_populates="agent_run", order_by="AgentStep.step_order")
    hypotheses: Mapped[list["DiagnosisHypothesis"]] = relationship(
        back_populates="agent_run",
        order_by="DiagnosisHypothesis.rank",
    )
    inspection_plan_items: Mapped[list["InspectionPlanItem"]] = relationship(
        back_populates="agent_run",
        order_by="InspectionPlanItem.item_order",
    )
    checklist_runs: Mapped[list["ChecklistRun"]] = relationship(back_populates="agent_run")
    report_drafts: Mapped[list["ReportDraft"]] = relationship(back_populates="agent_run")


class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "step_order", name="uq_agent_steps_run_order"),
        Index("idx_agent_steps_run", "agent_run_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent_run: Mapped[AgentRun] = relationship(back_populates="steps")


class DiagnosisHypothesis(Base):
    __tablename__ = "diagnosis_hypotheses"
    __table_args__ = (
        CheckConstraint("confidence_band IN ('HIGH','MEDIUM','LOW')", name="ck_diagnosis_hypotheses_confidence_band"),
        CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_diagnosis_hypotheses_risk_level"),
        UniqueConstraint("agent_run_id", "rank", name="uq_diagnosis_hypotheses_run_rank"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_next_checks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent_run: Mapped[AgentRun] = relationship(back_populates="hypotheses")
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="hypothesis")


class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    __table_args__ = (Index("idx_evidence_links_hypothesis", "hypothesis_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    hypothesis_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("diagnosis_hypotheses.id"))
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_code: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)

    hypothesis: Mapped[DiagnosisHypothesis | None] = relationship(back_populates="evidence_links")


class InspectionPlanItem(Base):
    __tablename__ = "inspection_plan_items"
    __table_args__ = (
        CheckConstraint(
            "safety_level IN ('NORMAL','CAUTION','APPROVAL_REQUIRED')",
            name="ck_inspection_plan_items_safety_level",
        ),
        UniqueConstraint("agent_run_id", "item_order", name="uq_inspection_plan_items_run_order"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False)
    item_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    expected_observation: Mapped[str | None] = mapped_column(Text)
    safety_level: Mapped[str] = mapped_column(String(40), nullable=False, default="NORMAL", server_default="NORMAL")
    evidence_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent_run: Mapped[AgentRun] = relationship(back_populates="inspection_plan_items")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(back_populates="source_inspection_plan_item")


class ChecklistRun(Base):
    __tablename__ = "checklist_runs"
    __table_args__ = (
        CheckConstraint("status IN ('CREATED','IN_PROGRESS','COMPLETED','BLOCKED')", name="ck_checklist_runs_status"),
        Index("idx_checklist_runs_tenant_session", "tenant_id", "diagnosis_session_id"),
        Index("idx_checklist_runs_agent_run", "tenant_id", "agent_run_id"),
        Index("idx_checklist_runs_tenant_status_updated", "tenant_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    diagnosis_session_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("diagnosis_sessions.id"), nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="CREATED", server_default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    diagnosis_session: Mapped[DiagnosisSession] = relationship(back_populates="checklist_runs")
    agent_run: Mapped[AgentRun] = relationship(back_populates="checklist_runs")
    created_by: Mapped[User] = relationship()
    items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="checklist_run",
        order_by="ChecklistItem.item_order",
    )
    report_drafts: Mapped[list["ReportDraft"]] = relationship(back_populates="checklist_run")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    __table_args__ = (
        CheckConstraint(
            "status IN ('TODO','IN_PROGRESS','DONE','BLOCKED','SKIPPED')",
            name="ck_checklist_items_status",
        ),
        UniqueConstraint("checklist_run_id", "item_order", name="uq_checklist_items_run_order"),
        Index("idx_checklist_items_run", "checklist_run_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    checklist_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("checklist_runs.id"), nullable=False)
    source_inspection_plan_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("inspection_plan_items.id"),
        nullable=False,
    )
    item_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="TODO", server_default="TODO")
    field_note: Mapped[str | None] = mapped_column(Text)
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    checklist_run: Mapped[ChecklistRun] = relationship(back_populates="items")
    source_inspection_plan_item: Mapped[InspectionPlanItem] = relationship(back_populates="checklist_items")
    completed_by: Mapped[User | None] = relationship()


class ReportDraft(Base):
    __tablename__ = "report_drafts"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','SUBMITTED','APPROVED','REJECTED')", name="ck_report_drafts_status"),
        Index("idx_report_drafts_tenant_session", "tenant_id", "diagnosis_session_id"),
        Index("idx_report_drafts_tenant_status", "tenant_id", "status"),
        Index("idx_report_drafts_tenant_status_updated", "tenant_id", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    diagnosis_session_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("diagnosis_sessions.id"), nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False)
    checklist_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("checklist_runs.id"), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    inspection_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    safety_notes: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="DRAFT", server_default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    diagnosis_session: Mapped[DiagnosisSession] = relationship(back_populates="report_drafts")
    agent_run: Mapped[AgentRun] = relationship(back_populates="report_drafts")
    checklist_run: Mapped[ChecklistRun] = relationship(back_populates="report_drafts")
    created_by: Mapped[User] = relationship()
    approvals: Mapped[list["ReportApproval"]] = relationship(back_populates="report_draft")


class ReportApproval(Base):
    __tablename__ = "report_approvals"
    __table_args__ = (
        CheckConstraint("decision IN ('APPROVED','REJECTED')", name="ck_report_approvals_decision"),
        Index("idx_report_approvals_report", "tenant_id", "report_draft_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    report_draft_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("report_drafts.id"), nullable=False)
    approver_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    report_draft: Mapped[ReportDraft] = relationship(back_populates="approvals")
    approver: Mapped[User] = relationship()


class EquipmentIncident(Base):
    __tablename__ = "equipment_incidents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN','TRIAGED','CHECKLIST_IN_PROGRESS','REPORT_SUBMITTED','APPROVED','CLOSED','CANCELLED')",
            name="ck_equipment_incidents_status",
        ),
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_equipment_incidents_severity"),
        UniqueConstraint("tenant_id", "case_number", name="uq_equipment_incidents_tenant_case_number"),
        Index("idx_equipment_incidents_tenant_status_updated", "tenant_id", "status", "updated_at"),
        Index("idx_equipment_incidents_tenant_updated_opened", "tenant_id", "updated_at", "opened_at"),
        Index("idx_equipment_incidents_equipment", "tenant_id", "equipment_id"),
        Index("idx_equipment_incidents_alarm_code", "tenant_id", "alarm_code"),
        Index("idx_equipment_incidents_severity", "tenant_id", "severity"),
        Index("idx_equipment_incidents_primary_alarm", "tenant_id", "primary_alarm_event_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tenants.id"), nullable=False)
    equipment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("equipment.id"), nullable=False)
    primary_alarm_event_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("equipment_alarm_events.id"),
    )
    diagnosis_session_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("diagnosis_sessions.id"))
    checklist_run_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("checklist_runs.id"))
    report_draft_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("report_drafts.id"))
    approval_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("report_approvals.id"))
    case_number: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    alarm_code: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="OPEN", server_default="OPEN")
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    assigned_role: Mapped[str | None] = mapped_column(String(80))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checklist_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment: Mapped[Equipment] = relationship(back_populates="incidents")
    primary_alarm_event: Mapped[EquipmentAlarmEvent | None] = relationship()
    diagnosis_session: Mapped[DiagnosisSession | None] = relationship()
    checklist_run: Mapped[ChecklistRun | None] = relationship()
    report_draft: Mapped[ReportDraft | None] = relationship()
    approval: Mapped[ReportApproval | None] = relationship()
    owner: Mapped[User | None] = relationship()
