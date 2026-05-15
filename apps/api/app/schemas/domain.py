from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


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


class IoPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    direction: Literal["DI", "DO"]
    signal_type: str
    description: str
    normal_state: bool | None = None
    related_alarm_code: str | None = None


class EthercatDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slave_no: int
    name: str
    expected_state: Literal["INIT", "PRE_OP", "SAFE_OP", "OP"]
    vendor_id: str | None = None
    product_code: str | None = None


class EquipmentDetailResponse(BaseModel):
    equipment: EquipmentSummary
    alarms: list[AlarmCodeRead]
    io_points: list[IoPointRead]
    ethercat_devices: list[EthercatDeviceRead]


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

