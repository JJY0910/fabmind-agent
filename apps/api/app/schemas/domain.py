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


class EquipmentListResponse(BaseModel):
    items: list[EquipmentSummary]


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
