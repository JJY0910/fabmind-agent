from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    is_active: bool


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class LineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class EquipmentFamilyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class EquipmentSummary(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    family: str
    status: str
    equipment_id: uuid.UUID | None = None
    equipment_code: str | None = None
    equipment_name: str | None = None
    equipment_type: str | None = None
    subsystem: str | None = None
    location: str | None = None
    line_code: str | None = None
    operational_status: str | None = None
    current_alarm_code: str | None = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None
    last_seen_at: datetime | None = None
    linked_diagnosis_session_id: uuid.UUID | None = None


class EquipmentListResponse(BaseModel):
    items: list[EquipmentSummary]
    total: int = 0
    limit: int = 0
    offset: int = 0


class AlarmCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    title: str
    description: str
    primary_signal: str | None = None
    recommended_first_check: str | None = None


class AlarmCodeListResponse(BaseModel):
    items: list[AlarmCodeRead]


class IoPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    direction: Literal["DI", "DO"]
    signal_type: str
    description: str
    normal_state: bool | None = None
    related_alarm_code: str | None = None


class IoPointListResponse(BaseModel):
    items: list[IoPointRead]


class EthercatDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slave_no: int
    name: str
    expected_state: Literal["INIT", "PRE_OP", "SAFE_OP", "OP"]
    vendor_id: str | None = None
    product_code: str | None = None


class EthercatDeviceListResponse(BaseModel):
    items: list[EthercatDeviceRead]


EquipmentDataSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AlarmEventStatus = Literal["ACTIVE", "ACKNOWLEDGED", "CLEARED"]


class CreateEquipmentAlarmEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: uuid.UUID | None = None
    equipment_code: str | None = Field(default=None, min_length=1, max_length=80)
    source_event_id: str | None = Field(default=None, max_length=160)
    alarm_code: str = Field(min_length=1, max_length=80)
    alarm_name: str | None = Field(default=None, max_length=240)
    severity: EquipmentDataSeverity
    event_status: AlarmEventStatus = "ACTIVE"
    occurred_at: datetime
    source_system: str = Field(min_length=1, max_length=120)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    diagnosis_session_id: uuid.UUID | None = None


class EquipmentAlarmEventRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    equipment_code: str
    source_event_id: str | None = None
    alarm_code: str
    alarm_name: str | None = None
    severity: EquipmentDataSeverity
    event_status: AlarmEventStatus
    occurred_at: datetime
    received_at: datetime
    source_system: str
    raw_payload: dict[str, Any]
    diagnosis_session_id: uuid.UUID | None = None


class EquipmentAlarmEventListResponse(BaseModel):
    items: list[EquipmentAlarmEventRead]
    total: int
    limit: int
    offset: int


class CreateEquipmentIOSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: uuid.UUID | None = None
    equipment_code: str | None = Field(default=None, min_length=1, max_length=80)
    source_snapshot_id: str | None = Field(default=None, max_length=160)
    captured_at: datetime
    source_system: str = Field(min_length=1, max_length=120)
    observed_inputs: dict[str, Any] = Field(default_factory=dict)
    observed_outputs: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class EquipmentIOSnapshotRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    equipment_code: str
    source_snapshot_id: str | None = None
    captured_at: datetime
    received_at: datetime
    source_system: str
    observed_inputs: dict[str, Any]
    observed_outputs: dict[str, Any]
    raw_payload: dict[str, Any]


class EquipmentIOSnapshotListResponse(BaseModel):
    items: list[EquipmentIOSnapshotRead]
    total: int
    limit: int
    offset: int


class CreateEquipmentEthercatStatusSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: uuid.UUID | None = None
    equipment_code: str | None = Field(default=None, min_length=1, max_length=80)
    source_snapshot_id: str | None = Field(default=None, max_length=160)
    captured_at: datetime
    source_system: str = Field(min_length=1, max_length=120)
    master_state: str = Field(min_length=1, max_length=40)
    slave_count: int = Field(ge=0)
    working_counter: int | None = Field(default=None, ge=0)
    link_status: str = Field(min_length=1, max_length=80)
    error_code: str | None = Field(default=None, max_length=120)
    error_summary: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class EquipmentEthercatStatusSnapshotRead(BaseModel):
    id: uuid.UUID
    equipment_id: uuid.UUID
    equipment_code: str
    source_snapshot_id: str | None = None
    captured_at: datetime
    received_at: datetime
    source_system: str
    master_state: str
    slave_count: int
    working_counter: int | None = None
    link_status: str
    error_code: str | None = None
    error_summary: str | None = None
    raw_payload: dict[str, Any]


class EquipmentEthercatStatusSnapshotListResponse(BaseModel):
    items: list[EquipmentEthercatStatusSnapshotRead]
    total: int
    limit: int
    offset: int


class EvidenceRead(BaseModel):
    id: str
    type: str
    title: str
    content: str


class EquipmentDetailResponse(BaseModel):
    equipment: EquipmentSummary
    alarms: list[AlarmCodeRead]
    io_points: list[IoPointRead]
    ethercat_devices: list[EthercatDeviceRead]
    document_chunks: list[EvidenceRead] = []


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    resource_type: str
    resource_id: uuid.UUID | None = None
    severity: Literal["INFO", "WARNING", "ERROR", "SECURITY"]
    payload: dict[str, Any] | None = None
    created_at: datetime


class AuditEventListResponse(BaseModel):
    items: list[AuditEventRead]


DiagnosisStatus = Literal["CREATED", "ANALYZING", "ANALYSIS_READY", "INSUFFICIENT_EVIDENCE", "CLOSED"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EthercatState = Literal["INIT", "PRE_OP", "SAFE_OP", "OP", "UNKNOWN"]


class CreateDiagnosisSessionRequest(BaseModel):
    equipment_id: uuid.UUID
    alarm_code: str = Field(min_length=1, max_length=80)
    symptom_summary: str = Field(min_length=1)
    log_excerpt: str | None = None
    ethercat_state: EthercatState | None = None
    io_snapshot: dict[str, bool] = Field(default_factory=dict)
    recent_action: str | None = None
    risk_level: RiskLevel = "LOW"


class DiagnosisSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    equipment_id: uuid.UUID
    created_by_user_id: uuid.UUID
    alarm_code: str
    symptom_summary: str
    log_excerpt: str | None = None
    ethercat_state: str | None = None
    io_snapshot: dict[str, bool]
    recent_action: str | None = None
    status: DiagnosisStatus
    risk_level: RiskLevel
    created_at: datetime
    updated_at: datetime


class DiagnosisSessionListResponse(BaseModel):
    items: list[DiagnosisSessionRead]


AgentRunStatus = Literal["COMPLETED", "INSUFFICIENT_EVIDENCE", "SAFETY_BLOCKED", "FAILED"]
AgentSafetyResult = Literal[
    "SAFE_READ_ONLY",
    "APPROVAL_REQUIRED_FOR_FORCE_ACTION",
    "POLICY_BLOCKED_RISKY_ACTION",
]
AgentStepStatus = Literal["COMPLETED", "NEEDS_MORE_EVIDENCE", "BLOCKED"]
ConfidenceBand = Literal["HIGH", "MEDIUM", "LOW"]
InspectionSafetyLevel = Literal["NORMAL", "CAUTION", "APPROVAL_REQUIRED"]


class AgentStepRead(BaseModel):
    id: uuid.UUID
    step_order: int
    name: str
    status: AgentStepStatus
    summary: str | None = None
    details: dict[str, Any] | None = None


class EvidenceLinkRead(BaseModel):
    id: uuid.UUID
    hypothesis_id: uuid.UUID | None = None
    source_type: str
    source_code: str
    title: str
    excerpt: str
    relevance_reason: str


class DiagnosisHypothesisRead(BaseModel):
    id: uuid.UUID
    rank: int
    title: str
    reasoning: str
    confidence_band: ConfidenceBand
    risk_level: RiskLevel
    evidence_ids: list[str]
    recommended_next_checks: list[str]


class InspectionPlanItemRead(BaseModel):
    id: uuid.UUID
    item_order: int
    title: str
    instruction: str
    expected_observation: str | None = None
    safety_level: InspectionSafetyLevel
    evidence_codes: list[str]


class AgentRunResult(BaseModel):
    run_id: uuid.UUID
    session_id: uuid.UUID
    status: AgentRunStatus
    mode: str
    safety_result: AgentSafetyResult
    risk_level: RiskLevel
    steps: list[AgentStepRead]
    hypotheses: list[DiagnosisHypothesisRead]
    evidence: list[EvidenceLinkRead]
    inspection_plan_items: list[InspectionPlanItemRead]


ChecklistRunStatus = Literal["CREATED", "IN_PROGRESS", "COMPLETED", "BLOCKED"]
ChecklistItemStatus = Literal["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "SKIPPED"]


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    checklist_run_id: uuid.UUID
    source_inspection_plan_item_id: uuid.UUID
    item_order: int
    title: str
    description: str
    expected_result: str | None = None
    status: ChecklistItemStatus
    field_note: str | None = None
    completed_by_user_id: uuid.UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChecklistRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    diagnosis_session_id: uuid.UUID
    agent_run_id: uuid.UUID
    created_by_user_id: uuid.UUID
    status: ChecklistRunStatus
    created_at: datetime
    updated_at: datetime
    items: list[ChecklistItemRead]


class UpdateChecklistItemRequest(BaseModel):
    status: ChecklistItemStatus | None = None
    field_note: str | None = None


class ChecklistRunSummary(BaseModel):
    checklist_run_id: uuid.UUID
    diagnosis_session_id: uuid.UUID
    equipment_code: str
    checklist_name: str
    status: ChecklistRunStatus
    total_items: int
    completed_items: int
    failed_items: int
    pending_items: int
    created_at: datetime
    updated_at: datetime


class ChecklistRunListResponse(BaseModel):
    items: list[ChecklistRunSummary]
    total: int
    limit: int
    offset: int


ReportDraftStatus = Literal["DRAFT", "SUBMITTED", "APPROVED", "REJECTED"]
ReportDecision = Literal["APPROVED", "REJECTED"]


class ReportApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    report_draft_id: uuid.UUID
    approver_user_id: uuid.UUID
    decision: ReportDecision
    comment: str | None = None
    decided_at: datetime
    created_at: datetime


class ReportDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    diagnosis_session_id: uuid.UUID
    agent_run_id: uuid.UUID
    checklist_run_id: uuid.UUID
    created_by_user_id: uuid.UUID
    title: str
    summary: str
    root_cause: str
    evidence_summary: str
    inspection_summary: str
    recommended_action: str
    safety_notes: str
    status: ReportDraftStatus
    created_at: datetime
    updated_at: datetime
    approvals: list[ReportApprovalRead] = Field(default_factory=list)


class ReportApprovalRequest(BaseModel):
    comment: str | None = None


class ReportRejectionRequest(BaseModel):
    comment: str = Field(min_length=1)


class ReportDraftSummary(BaseModel):
    report_draft_id: uuid.UUID
    diagnosis_session_id: uuid.UUID
    equipment_code: str
    status: ReportDraftStatus
    root_cause_summary: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None


class ReportDraftListResponse(BaseModel):
    items: list[ReportDraftSummary]
    total: int
    limit: int
    offset: int


class ApprovalQueueItem(BaseModel):
    approval_id: uuid.UUID | None = None
    report_draft_id: uuid.UUID
    approval_status: str
    requested_by: str
    reviewer_id: uuid.UUID | None = None
    reviewer_role: str | None = None
    requested_at: datetime
    reviewed_at: datetime | None = None
    reviewer_comment: str | None = None
    rejection_reason: str | None = None


class ApprovalQueueResponse(BaseModel):
    items: list[ApprovalQueueItem]
    total: int
    limit: int
    offset: int


IncidentStatus = Literal[
    "OPEN",
    "TRIAGED",
    "CHECKLIST_IN_PROGRESS",
    "REPORT_SUBMITTED",
    "APPROVED",
    "CLOSED",
    "CANCELLED",
]


class CreateIncidentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: uuid.UUID | None = None
    equipment_code: str | None = Field(default=None, min_length=1, max_length=80)
    primary_alarm_event_id: uuid.UUID | None = None
    diagnosis_session_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1)
    alarm_code: str = Field(min_length=1, max_length=80)
    severity: RiskLevel
    assigned_role: str | None = Field(default="FIELD_ENGINEER", max_length=80)


class UpdateIncidentStatusRequest(BaseModel):
    status: IncidentStatus


class UpdateIncidentLinksRequest(BaseModel):
    diagnosis_session_id: uuid.UUID | None = None
    checklist_run_id: uuid.UUID | None = None
    report_draft_id: uuid.UUID | None = None
    approval_id: uuid.UUID | None = None


class IncidentSummary(BaseModel):
    incident_id: uuid.UUID
    equipment_id: uuid.UUID
    equipment_code: str
    case_number: str | None = None
    primary_alarm_event_id: uuid.UUID | None = None
    alarm_code: str
    title: str
    summary: str
    risk_level: RiskLevel
    status: IncidentStatus
    opened_at: datetime
    updated_at: datetime
    triaged_at: datetime | None = None
    checklist_started_at: datetime | None = None
    report_submitted_at: datetime | None = None
    approved_at: datetime | None = None
    closed_at: datetime | None = None
    owner: str | None = None
    assigned_role: str | None = None
    diagnosis_session_id: uuid.UUID | None = None
    linked_checklist_run_id: uuid.UUID | None = None
    linked_report_draft_id: uuid.UUID | None = None
    linked_approval_id: uuid.UUID | None = None


class IncidentListResponse(BaseModel):
    items: list[IncidentSummary]
    total: int
    limit: int
    offset: int


class SystemSafetySettingsResponse(BaseModel):
    external_ai_enabled: bool
    equipment_control_enabled: bool
    interlock_bypass_allowed: bool
    output_forcing_allowed: bool
    human_approval_required: bool
    audit_logging_enabled: bool
    deterministic_engine_enabled: bool
    allowed_equipment_scope: list[str]
    policy_version: str
    generated_at: datetime


class DashboardRecentDiagnosisSession(BaseModel):
    session_id: uuid.UUID
    equipment_code: str
    alarm_code: str
    status: DiagnosisStatus
    risk_level: RiskLevel
    created_at: datetime


class DashboardRequiredAction(BaseModel):
    action_type: str
    resource_type: str
    resource_id: uuid.UUID
    title: str
    severity: str
    created_at: datetime | None = None


class DashboardSummaryResponse(BaseModel):
    active_diagnosis_count: int
    pending_approval_count: int
    high_risk_count: int
    evidence_linked_rate: float
    open_checklist_count: int
    submitted_report_count: int
    approved_report_count: int
    recent_diagnosis_sessions: list[DashboardRecentDiagnosisSession]
    required_actions: list[DashboardRequiredAction]
    guardrail_blocks_today: int
