from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Equipment,
    EquipmentAlarmEvent,
    EquipmentEthercatStatusSnapshot,
    EquipmentIOSnapshot,
    User,
)
from app.services.audit import create_audit_event
from app.services.incidents import create_or_link_incident_from_alarm_event


class EquipmentDataAdapterError(ValueError):
    pass


class UnsafeEquipmentDataPayloadError(EquipmentDataAdapterError):
    pass


class EquipmentDataNotFoundError(EquipmentDataAdapterError):
    pass


UNSAFE_INTENT_KEYS = {
    "command",
    "command_intent",
    "control",
    "control_request",
    "requested_action",
    "requested_command",
    "desired_state",
    "target_state",
    "operation_request",
    "motion_request",
    "motion_command",
    "reset_command",
    "reset_request",
    "output_command",
    "output_write_request",
    "force_output_request",
    "write_output_request",
    "interlock_override",
    "override_request",
    "servo_command",
    "servo_request",
    "write_request",
}
INTENT_VALUE_KEYS = {
    "action",
    "intent",
    "instruction",
    "operation",
    "requested_state",
    "requested_action",
    "desired_state",
    "target_state",
}
UNSAFE_VALUE_MARKERS = (
    "force output",
    "write output",
    "bypass",
    "override",
    "servo on",
    "motion",
    "reset command",
)


class ReadOnlyEquipmentDataAdapter:
    """Inbound telemetry adapter. It has no equipment command channel."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest_alarm_event(self, *, actor: User, payload: Any) -> EquipmentAlarmEvent:
        self._validate_read_only_payload(payload.model_dump(exclude_none=True))
        equipment = self._resolve_equipment(actor.tenant_id, payload.equipment_id, payload.equipment_code)
        event = EquipmentAlarmEvent(
            tenant_id=actor.tenant_id,
            equipment_id=equipment.id,
            diagnosis_session_id=payload.diagnosis_session_id,
            source_event_id=payload.source_event_id,
            alarm_code=payload.alarm_code,
            alarm_name=payload.alarm_name,
            severity=payload.severity,
            event_status=payload.event_status,
            occurred_at=payload.occurred_at,
            received_at=datetime.now(UTC),
            source_system=payload.source_system,
            raw_payload=payload.raw_payload,
            equipment=equipment,
        )
        self.db.add(event)
        self.db.flush()
        create_audit_event(
            self.db,
            tenant_id=actor.tenant_id,
            actor_user_id=actor.id,
            event_type="EQUIPMENT_ALARM_EVENT_INGESTED",
            resource_type="equipment_alarm_event",
            resource_id=event.id,
            severity="INFO",
            payload={
                "equipment_code": equipment.code,
                "alarm_code": event.alarm_code,
                "source_system": event.source_system,
            },
        )
        create_or_link_incident_from_alarm_event(self.db, actor=actor, event=event, equipment=equipment)
        self.db.flush()
        return event

    def ingest_io_snapshot(self, *, actor: User, payload: Any) -> EquipmentIOSnapshot:
        self._validate_read_only_payload(payload.model_dump(exclude_none=True))
        equipment = self._resolve_equipment(actor.tenant_id, payload.equipment_id, payload.equipment_code)
        snapshot = EquipmentIOSnapshot(
            tenant_id=actor.tenant_id,
            equipment_id=equipment.id,
            source_snapshot_id=payload.source_snapshot_id,
            captured_at=payload.captured_at,
            received_at=datetime.now(UTC),
            source_system=payload.source_system,
            observed_inputs=payload.observed_inputs,
            observed_outputs=payload.observed_outputs,
            raw_payload=payload.raw_payload,
            equipment=equipment,
        )
        self.db.add(snapshot)
        self.db.flush()
        create_audit_event(
            self.db,
            tenant_id=actor.tenant_id,
            actor_user_id=actor.id,
            event_type="EQUIPMENT_IO_SNAPSHOT_INGESTED",
            resource_type="equipment_io_snapshot",
            resource_id=snapshot.id,
            severity="INFO",
            payload={
                "equipment_code": equipment.code,
                "source_system": snapshot.source_system,
                "input_count": len(snapshot.observed_inputs),
                "observed_output_count": len(snapshot.observed_outputs),
            },
        )
        self.db.flush()
        return snapshot

    def ingest_ethercat_status_snapshot(
        self,
        *,
        actor: User,
        payload: Any,
    ) -> EquipmentEthercatStatusSnapshot:
        self._validate_read_only_payload(payload.model_dump(exclude_none=True))
        equipment = self._resolve_equipment(actor.tenant_id, payload.equipment_id, payload.equipment_code)
        snapshot = EquipmentEthercatStatusSnapshot(
            tenant_id=actor.tenant_id,
            equipment_id=equipment.id,
            source_snapshot_id=payload.source_snapshot_id,
            captured_at=payload.captured_at,
            received_at=datetime.now(UTC),
            source_system=payload.source_system,
            master_state=payload.master_state,
            slave_count=payload.slave_count,
            working_counter=payload.working_counter,
            link_status=payload.link_status,
            error_code=payload.error_code,
            error_summary=payload.error_summary,
            raw_payload=payload.raw_payload,
            equipment=equipment,
        )
        self.db.add(snapshot)
        self.db.flush()
        create_audit_event(
            self.db,
            tenant_id=actor.tenant_id,
            actor_user_id=actor.id,
            event_type="ETHERCAT_STATUS_SNAPSHOT_INGESTED",
            resource_type="equipment_ethercat_status_snapshot",
            resource_id=snapshot.id,
            severity="INFO",
            payload={
                "equipment_code": equipment.code,
                "master_state": snapshot.master_state,
                "source_system": snapshot.source_system,
            },
        )
        self.db.flush()
        return snapshot

    def _resolve_equipment(
        self,
        tenant_id: uuid.UUID,
        equipment_id: uuid.UUID | None,
        equipment_code: str | None,
    ) -> Equipment:
        if equipment_id is None and equipment_code is None:
            raise EquipmentDataAdapterError("equipment_id or equipment_code is required")

        filters = [Equipment.tenant_id == tenant_id]
        if equipment_id is not None:
            filters.append(Equipment.id == equipment_id)
        if equipment_code is not None:
            filters.append(Equipment.code == equipment_code)

        equipment = self.db.scalar(select(Equipment).where(*filters))
        if equipment is None:
            raise EquipmentDataNotFoundError("Equipment not found for tenant")
        return equipment

    def _validate_read_only_payload(self, payload: Mapping[str, Any]) -> None:
        unsafe_path = _find_unsafe_intent(payload)
        if unsafe_path is not None:
            raise UnsafeEquipmentDataPayloadError(
                f"Read-only equipment ingestion rejected command-like intent at {unsafe_path}"
            )


def _find_unsafe_intent(value: Any, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = _normalize_key(str(key))
            child_path = f"{path}.{key}"
            if normalized in UNSAFE_INTENT_KEYS:
                return child_path
            if normalized in INTENT_VALUE_KEYS and _contains_unsafe_marker(child):
                return child_path
            nested = _find_unsafe_intent(child, child_path)
            if nested is not None:
                return nested
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nested = _find_unsafe_intent(child, f"{path}[{index}]")
            if nested is not None:
                return nested
    return None


def _contains_unsafe_marker(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.lower()
        return any(marker in normalized for marker in UNSAFE_VALUE_MARKERS)
    if isinstance(value, Mapping):
        return any(_contains_unsafe_marker(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_unsafe_marker(child) for child in value)
    return False


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")
