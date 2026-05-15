from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import ROLE_ADMIN, ROLE_FIELD, ROLE_SENIOR, require_roles
from app.db.session import get_db
from app.models import AlarmCode, Equipment, EthercatDevice, IoPoint, User
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
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentListResponse:
    equipment = db.scalars(
        select(Equipment)
        .options(joinedload(Equipment.family))
        .where(Equipment.tenant_id == current_user.tenant_id)
        .order_by(Equipment.code)
    ).all()
    return EquipmentListResponse(items=[_equipment_summary(item) for item in equipment])


@router.get("/equipment/{equipment_id}", response_model=EquipmentDetailResponse)
def get_equipment_detail(
    equipment_id: uuid.UUID,
    current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> EquipmentDetailResponse:
    equipment = db.scalar(
        select(Equipment)
        .options(joinedload(Equipment.family))
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
        equipment=_equipment_summary(equipment),
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


def _equipment_summary(equipment: Equipment) -> EquipmentSummary:
    return EquipmentSummary(
        id=equipment.id,
        code=equipment.code,
        name=equipment.name,
        family=equipment.family.code,
        status=equipment.status,
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

