from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import (
    Equipment,
    EquipmentAlarmEvent,
    EquipmentEthercatStatusSnapshot,
    EquipmentIOSnapshot,
    User,
)
from app.schemas import (
    CreateEquipmentAlarmEventRequest,
    CreateEquipmentEthercatStatusSnapshotRequest,
    CreateEquipmentIOSnapshotRequest,
    EquipmentAlarmEventListResponse,
    EquipmentAlarmEventRead,
    EquipmentEthercatStatusSnapshotListResponse,
    EquipmentEthercatStatusSnapshotRead,
    EquipmentIOSnapshotListResponse,
    EquipmentIOSnapshotRead,
)
from app.services.audit import create_audit_event
from app.services.equipment_data_adapter import (
    EquipmentDataAdapterError,
    EquipmentDataNotFoundError,
    ReadOnlyEquipmentDataAdapter,
    UnsafeEquipmentDataPayloadError,
)


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)
INGESTION_ROLES = (ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(prefix="/equipment-data", tags=["equipment-data"])


@router.post(
    "/alarm-events",
    response_model=EquipmentAlarmEventRead,
    status_code=status.HTTP_201_CREATED,
)
def ingest_alarm_event(
    payload: CreateEquipmentAlarmEventRequest,
    current_user: User = Depends(require_roles(*INGESTION_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentAlarmEventRead:
    adapter = ReadOnlyEquipmentDataAdapter(db)
    try:
        event = adapter.ingest_alarm_event(actor=current_user, payload=payload)
    except UnsafeEquipmentDataPayloadError as exc:
        _audit_blocked_ingestion(db, current_user, "equipment_alarm_event", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EquipmentDataNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EquipmentDataAdapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(event)
    return _alarm_event_read(event)


@router.get("/alarm-events", response_model=EquipmentAlarmEventListResponse)
def list_alarm_events(
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    severity: str | None = None,
    risk_level: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentAlarmEventListResponse:
    filters = [EquipmentAlarmEvent.tenant_id == current_user.tenant_id]
    if equipment_id:
        filters.append(EquipmentAlarmEvent.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)
    if severity or risk_level:
        filters.append(EquipmentAlarmEvent.severity == (severity or risk_level))
    if status_filter:
        filters.append(EquipmentAlarmEvent.event_status == status_filter)

    total = (
        db.scalar(
            select(func.count())
            .select_from(EquipmentAlarmEvent)
            .join(Equipment, EquipmentAlarmEvent.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    events = db.scalars(
        select(EquipmentAlarmEvent)
        .join(Equipment, EquipmentAlarmEvent.equipment_id == Equipment.id)
        .options(joinedload(EquipmentAlarmEvent.equipment))
        .where(*filters)
        .order_by(EquipmentAlarmEvent.occurred_at.desc(), EquipmentAlarmEvent.received_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return EquipmentAlarmEventListResponse(
        items=[_alarm_event_read(event) for event in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/io-snapshots",
    response_model=EquipmentIOSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def ingest_io_snapshot(
    payload: CreateEquipmentIOSnapshotRequest,
    current_user: User = Depends(require_roles(*INGESTION_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentIOSnapshotRead:
    adapter = ReadOnlyEquipmentDataAdapter(db)
    try:
        snapshot = adapter.ingest_io_snapshot(actor=current_user, payload=payload)
    except UnsafeEquipmentDataPayloadError as exc:
        _audit_blocked_ingestion(db, current_user, "equipment_io_snapshot", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EquipmentDataNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EquipmentDataAdapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(snapshot)
    return _io_snapshot_read(snapshot)


@router.get("/io-snapshots", response_model=EquipmentIOSnapshotListResponse)
def list_io_snapshots(
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentIOSnapshotListResponse:
    filters = [EquipmentIOSnapshot.tenant_id == current_user.tenant_id]
    if equipment_id:
        filters.append(EquipmentIOSnapshot.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)

    total = (
        db.scalar(
            select(func.count())
            .select_from(EquipmentIOSnapshot)
            .join(Equipment, EquipmentIOSnapshot.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    snapshots = db.scalars(
        select(EquipmentIOSnapshot)
        .join(Equipment, EquipmentIOSnapshot.equipment_id == Equipment.id)
        .options(joinedload(EquipmentIOSnapshot.equipment))
        .where(*filters)
        .order_by(EquipmentIOSnapshot.captured_at.desc(), EquipmentIOSnapshot.received_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return EquipmentIOSnapshotListResponse(
        items=[_io_snapshot_read(snapshot) for snapshot in snapshots],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/ethercat-status-snapshots",
    response_model=EquipmentEthercatStatusSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def ingest_ethercat_status_snapshot(
    payload: CreateEquipmentEthercatStatusSnapshotRequest,
    current_user: User = Depends(require_roles(*INGESTION_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentEthercatStatusSnapshotRead:
    adapter = ReadOnlyEquipmentDataAdapter(db)
    try:
        snapshot = adapter.ingest_ethercat_status_snapshot(actor=current_user, payload=payload)
    except UnsafeEquipmentDataPayloadError as exc:
        _audit_blocked_ingestion(db, current_user, "equipment_ethercat_status_snapshot", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EquipmentDataNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EquipmentDataAdapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(snapshot)
    return _ethercat_snapshot_read(snapshot)


@router.get("/ethercat-status-snapshots", response_model=EquipmentEthercatStatusSnapshotListResponse)
def list_ethercat_status_snapshots(
    equipment_id: uuid.UUID | None = None,
    equipment_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentEthercatStatusSnapshotListResponse:
    filters = [EquipmentEthercatStatusSnapshot.tenant_id == current_user.tenant_id]
    if equipment_id:
        filters.append(EquipmentEthercatStatusSnapshot.equipment_id == equipment_id)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)

    total = (
        db.scalar(
            select(func.count())
            .select_from(EquipmentEthercatStatusSnapshot)
            .join(Equipment, EquipmentEthercatStatusSnapshot.equipment_id == Equipment.id)
            .where(*filters)
        )
        or 0
    )
    snapshots = db.scalars(
        select(EquipmentEthercatStatusSnapshot)
        .join(Equipment, EquipmentEthercatStatusSnapshot.equipment_id == Equipment.id)
        .options(joinedload(EquipmentEthercatStatusSnapshot.equipment))
        .where(*filters)
        .order_by(
            EquipmentEthercatStatusSnapshot.captured_at.desc(),
            EquipmentEthercatStatusSnapshot.received_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return EquipmentEthercatStatusSnapshotListResponse(
        items=[_ethercat_snapshot_read(snapshot) for snapshot in snapshots],
        total=total,
        limit=limit,
        offset=offset,
    )


def _audit_blocked_ingestion(db: Session, current_user: User, resource_type: str, reason: str) -> None:
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="EQUIPMENT_DATA_INGESTION_BLOCKED",
        resource_type=resource_type,
        severity="SECURITY",
        payload={"reason": reason},
    )
    db.commit()


def _alarm_event_read(event: EquipmentAlarmEvent) -> EquipmentAlarmEventRead:
    return EquipmentAlarmEventRead(
        id=event.id,
        equipment_id=event.equipment_id,
        equipment_code=event.equipment.code,
        source_event_id=event.source_event_id,
        alarm_code=event.alarm_code,
        alarm_name=event.alarm_name,
        severity=event.severity,
        event_status=event.event_status,
        occurred_at=event.occurred_at,
        received_at=event.received_at,
        source_system=event.source_system,
        raw_payload=event.raw_payload,
        diagnosis_session_id=event.diagnosis_session_id,
    )


def _io_snapshot_read(snapshot: EquipmentIOSnapshot) -> EquipmentIOSnapshotRead:
    return EquipmentIOSnapshotRead(
        id=snapshot.id,
        equipment_id=snapshot.equipment_id,
        equipment_code=snapshot.equipment.code,
        source_snapshot_id=snapshot.source_snapshot_id,
        captured_at=snapshot.captured_at,
        received_at=snapshot.received_at,
        source_system=snapshot.source_system,
        observed_inputs=snapshot.observed_inputs,
        observed_outputs=snapshot.observed_outputs,
        raw_payload=snapshot.raw_payload,
    )


def _ethercat_snapshot_read(
    snapshot: EquipmentEthercatStatusSnapshot,
) -> EquipmentEthercatStatusSnapshotRead:
    return EquipmentEthercatStatusSnapshotRead(
        id=snapshot.id,
        equipment_id=snapshot.equipment_id,
        equipment_code=snapshot.equipment.code,
        source_snapshot_id=snapshot.source_snapshot_id,
        captured_at=snapshot.captured_at,
        received_at=snapshot.received_at,
        source_system=snapshot.source_system,
        master_state=snapshot.master_state,
        slave_count=snapshot.slave_count,
        working_counter=snapshot.working_counter,
        link_status=snapshot.link_status,
        error_code=snapshot.error_code,
        error_summary=snapshot.error_summary,
        raw_payload=snapshot.raw_payload,
    )
