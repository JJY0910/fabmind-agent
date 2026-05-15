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
