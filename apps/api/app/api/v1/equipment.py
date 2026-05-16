from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import AlarmCode, DiagnosisSession, Equipment, EthercatDevice, IoPoint, Line, User
from app.schemas import (
    AlarmCodeListResponse,
    AlarmCodeRead,
    EquipmentDetailResponse,
    EquipmentListResponse,
    EquipmentSummary,
    EthercatDeviceListResponse,
    EthercatDeviceRead,
    IoPointListResponse,
    IoPointRead,
)
from app.services.audit import create_audit_event


READ_ROLES = (ROLE_FIELD, ROLE_SENIOR, ROLE_ADMIN)

router = APIRouter(tags=["equipment-knowledge"])


@router.get("/equipment", response_model=EquipmentListResponse)
def list_equipment(
    status_filter: str | None = Query(default=None, alias="status"),
    equipment_code: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentListResponse:
    filters = [Equipment.tenant_id == current_user.tenant_id]
    if status_filter:
        filters.append(Equipment.status == status_filter)
    if equipment_code:
        filters.append(Equipment.code == equipment_code)

    total = db.scalar(select(func.count()).select_from(Equipment).where(*filters)) or 0
    equipment = db.scalars(
        select(Equipment)
        .options(joinedload(Equipment.family), joinedload(Equipment.line).joinedload(Line.site))
        .where(*filters)
        .order_by(Equipment.code)
        .limit(limit)
        .offset(offset)
    ).all()
    latest_sessions = _latest_sessions_by_equipment(db, current_user.tenant_id, [item.id for item in equipment])
    return EquipmentListResponse(
        items=[_equipment_summary(item, latest_sessions.get(item.id)) for item in equipment],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/equipment/{equipment_id}", response_model=EquipmentDetailResponse)
def get_equipment_detail(
    equipment_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentDetailResponse:
    equipment = db.scalar(
        select(Equipment)
        .options(joinedload(Equipment.family), joinedload(Equipment.line).joinedload(Line.site))
        .where(Equipment.id == equipment_id, Equipment.tenant_id == current_user.tenant_id)
    )
    if equipment is None:
        _audit_cross_tenant_equipment_attempt(db, current_user, equipment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")

    alarms = db.scalars(
        select(AlarmCode)
        .where(AlarmCode.tenant_id == current_user.tenant_id, AlarmCode.equipment_family_id == equipment.family_id)
        .order_by(AlarmCode.code)
    ).all()
    io_points = db.scalars(
        select(IoPoint)
        .where(IoPoint.tenant_id == current_user.tenant_id, IoPoint.equipment_id == equipment.id)
        .order_by(IoPoint.code)
    ).all()
    ethercat_devices = db.scalars(
        select(EthercatDevice)
        .where(EthercatDevice.tenant_id == current_user.tenant_id, EthercatDevice.equipment_id == equipment.id)
        .order_by(EthercatDevice.slave_no)
    ).all()

    response = EquipmentDetailResponse(
        equipment=_equipment_summary(equipment, _latest_session_for_equipment(db, current_user.tenant_id, equipment.id)),
        alarms=[AlarmCodeRead.model_validate(alarm) for alarm in alarms],
        io_points=[IoPointRead.model_validate(point) for point in io_points],
        ethercat_devices=[EthercatDeviceRead.model_validate(device) for device in ethercat_devices],
        document_chunks=[],
    )
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="EQUIPMENT_DETAIL_VIEWED",
        resource_type="equipment",
        resource_id=equipment.id,
        severity="INFO",
        payload={"equipment_code": equipment.code},
    )
    db.commit()
    return response


@router.get("/alarms", response_model=AlarmCodeListResponse)
def list_alarms(
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> AlarmCodeListResponse:
    alarms = db.scalars(
        select(AlarmCode).where(AlarmCode.tenant_id == current_user.tenant_id).order_by(AlarmCode.code)
    ).all()
    return AlarmCodeListResponse(items=[AlarmCodeRead.model_validate(alarm) for alarm in alarms])


@router.get("/io-points", response_model=IoPointListResponse)
def list_io_points(
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> IoPointListResponse:
    io_points = db.scalars(
        select(IoPoint).where(IoPoint.tenant_id == current_user.tenant_id).order_by(IoPoint.code)
    ).all()
    return IoPointListResponse(items=[IoPointRead.model_validate(point) for point in io_points])


@router.get("/ethercat-devices", response_model=EthercatDeviceListResponse)
def list_ethercat_devices(
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EthercatDeviceListResponse:
    devices = db.scalars(
        select(EthercatDevice)
        .where(EthercatDevice.tenant_id == current_user.tenant_id)
        .order_by(EthercatDevice.equipment_id, EthercatDevice.slave_no)
    ).all()
    return EthercatDeviceListResponse(items=[EthercatDeviceRead.model_validate(device) for device in devices])


def _equipment_summary(equipment: Equipment, latest_session: DiagnosisSession | None = None) -> EquipmentSummary:
    location = None
    line_code = None
    if equipment.line is not None:
        line_code = equipment.line.code
        location = line_code
        if equipment.line.site is not None:
            location = f"{equipment.line.site.code} / {equipment.line.code}"

    return EquipmentSummary(
        id=equipment.id,
        code=equipment.code,
        name=equipment.name,
        family=equipment.family.code,
        status=equipment.status,
        equipment_id=equipment.id,
        equipment_code=equipment.code,
        equipment_name=equipment.name,
        equipment_type=equipment.family.name,
        subsystem="FOUP Clamp / EtherCAT I/O",
        location=location,
        line_code=line_code,
        operational_status=equipment.status,
        current_alarm_code=latest_session.alarm_code if latest_session is not None else None,
        risk_level=latest_session.risk_level if latest_session is not None else None,
        last_seen_at=latest_session.updated_at if latest_session is not None else equipment.created_at,
        linked_diagnosis_session_id=latest_session.id if latest_session is not None else None,
    )


def _latest_sessions_by_equipment(
    db: Session,
    tenant_id: uuid.UUID,
    equipment_ids: list[uuid.UUID],
) -> dict[uuid.UUID, DiagnosisSession]:
    if not equipment_ids:
        return {}
    sessions = db.scalars(
        select(DiagnosisSession)
        .where(DiagnosisSession.tenant_id == tenant_id, DiagnosisSession.equipment_id.in_(equipment_ids))
        .order_by(DiagnosisSession.updated_at.desc(), DiagnosisSession.created_at.desc())
    ).all()
    latest: dict[uuid.UUID, DiagnosisSession] = {}
    for session in sessions:
        latest.setdefault(session.equipment_id, session)
    return latest


def _latest_session_for_equipment(db: Session, tenant_id: uuid.UUID, equipment_id: uuid.UUID) -> DiagnosisSession | None:
    return db.scalar(
        select(DiagnosisSession)
        .where(DiagnosisSession.tenant_id == tenant_id, DiagnosisSession.equipment_id == equipment_id)
        .order_by(DiagnosisSession.updated_at.desc(), DiagnosisSession.created_at.desc())
        .limit(1)
    )


def _audit_cross_tenant_equipment_attempt(db: Session, current_user: User, equipment_id: uuid.UUID) -> None:
    equipment = db.scalar(select(Equipment).where(Equipment.id == equipment_id))
    if equipment is None:
        return
    create_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        event_type="EQUIPMENT_ACCESS_DENIED",
        resource_type="equipment",
        resource_id=equipment_id,
        severity="SECURITY",
        payload={"reason": "cross_tenant_or_not_visible"},
    )
    db.commit()
