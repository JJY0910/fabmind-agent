from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed import deterministic_uuid, seed_database
from app.models import (
    AlarmCode,
    AuditEvent,
    Equipment,
    EquipmentFamily,
    EthercatDevice,
    IoPoint,
    Line,
    Site,
    Tenant,
    User,
)
from app.schemas import (
    AlarmCodeRead,
    AuditEventListResponse,
    AuditEventRead,
    EquipmentDetailResponse,
    EquipmentListResponse,
    EquipmentSummary,
    EthercatDeviceRead,
    IoPointRead,
)


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with testing_session() as session:
        seed_database(session)
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_seed_integrity(db_session: Session):
    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1
    assert db_session.scalar(select(func.count()).select_from(User)) == 3
    assert db_session.scalar(select(func.count()).select_from(EquipmentFamily)) == 1
    assert db_session.scalar(select(func.count()).select_from(Equipment)) == 3
    assert db_session.scalar(select(func.count()).select_from(AlarmCode)) == 30
    assert db_session.scalar(select(func.count()).select_from(IoPoint)) == 60
    assert db_session.scalar(select(func.count()).select_from(EthercatDevice)) >= 6
    assert db_session.scalar(select(func.count()).select_from(AuditEvent)) == 1

    seed_database(db_session)

    assert db_session.scalar(select(func.count()).select_from(User)) == 3
    assert db_session.scalar(select(func.count()).select_from(Equipment)) == 3
    assert db_session.scalar(select(func.count()).select_from(AlarmCode)) == 30
    assert db_session.scalar(select(func.count()).select_from(IoPoint)) == 60


def test_equipment_list_query(db_session: Session):
    tenant = _tenant(db_session)
    equipment = db_session.scalars(
        select(Equipment).where(Equipment.tenant_id == tenant.id).order_by(Equipment.code)
    ).all()

    response = EquipmentListResponse(
        items=[
            EquipmentSummary(
                id=item.id,
                code=item.code,
                name=item.name,
                family=item.family.code,
                status=item.status,
            )
            for item in equipment
        ]
    )

    assert [item.code for item in response.items] == ["LP-01", "LP-02", "LP-03"]
    assert {item.family for item in response.items} == {"LOAD_PORT_FOUP_CLAMP"}


def test_equipment_detail_query(db_session: Session):
    tenant = _tenant(db_session)
    equipment = db_session.scalar(
        select(Equipment).where(Equipment.tenant_id == tenant.id, Equipment.code == "LP-01")
    )
    assert equipment is not None

    alarms = db_session.scalars(
        select(AlarmCode)
        .where(AlarmCode.tenant_id == tenant.id, AlarmCode.equipment_family_id == equipment.family_id)
        .order_by(AlarmCode.code)
    ).all()
    io_points = db_session.scalars(
        select(IoPoint).where(IoPoint.tenant_id == tenant.id, IoPoint.equipment_id == equipment.id).order_by(IoPoint.code)
    ).all()
    ethercat_devices = db_session.scalars(
        select(EthercatDevice)
        .where(EthercatDevice.tenant_id == tenant.id, EthercatDevice.equipment_id == equipment.id)
        .order_by(EthercatDevice.slave_no)
    ).all()

    response = EquipmentDetailResponse(
        equipment=EquipmentSummary(
            id=equipment.id,
            code=equipment.code,
            name=equipment.name,
            family=equipment.family.code,
            status=equipment.status,
        ),
        alarms=[AlarmCodeRead.model_validate(alarm) for alarm in alarms],
        io_points=[IoPointRead.model_validate(point) for point in io_points],
        ethercat_devices=[EthercatDeviceRead.model_validate(device) for device in ethercat_devices],
    )

    assert response.equipment.code == "LP-01"
    assert len(response.alarms) == 30
    assert len(response.io_points) == 30
    assert len(response.ethercat_devices) == 2


def test_alarm_list_query(db_session: Session):
    tenant = _tenant(db_session)
    alarms = db_session.scalars(
        select(AlarmCode).where(AlarmCode.tenant_id == tenant.id).order_by(AlarmCode.code)
    ).all()
    response = [AlarmCodeRead.model_validate(alarm) for alarm in alarms]

    assert len(response) == 30
    assert response[0].code == "ECAT-STATE-021"
    assert {alarm.severity for alarm in response} <= {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_io_list_query(db_session: Session):
    tenant = _tenant(db_session)
    equipment = db_session.scalar(
        select(Equipment).where(Equipment.tenant_id == tenant.id, Equipment.code == "LP-02")
    )
    assert equipment is not None

    io_points = db_session.scalars(
        select(IoPoint).where(IoPoint.tenant_id == tenant.id, IoPoint.equipment_id == equipment.id).order_by(IoPoint.code)
    ).all()
    response = [IoPointRead.model_validate(point) for point in io_points]

    assert len(response) == 30
    assert {point.direction for point in response} == {"DI", "DO"}
    assert all(point.related_alarm_code for point in response)


def test_tenant_isolation(db_session: Session):
    primary_tenant = _tenant(db_session)
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "OTHER_TENANT"),
        code="OTHER_TENANT",
        name="Other Synthetic Tenant",
    )
    other_site = Site(
        id=deterministic_uuid("site", other_tenant.code, "SITE-B"),
        tenant_id=other_tenant.id,
        code="SITE-B",
        name="Other Site",
    )
    other_line = Line(
        id=deterministic_uuid("line", other_tenant.code, "LINE-B"),
        tenant_id=other_tenant.id,
        site_id=other_site.id,
        code="LINE-B",
        name="Other Line",
    )
    other_family = EquipmentFamily(
        id=deterministic_uuid("equipment_family", other_tenant.code, "LOAD_PORT_FOUP_CLAMP"),
        tenant_id=other_tenant.id,
        code="LOAD_PORT_FOUP_CLAMP",
        name="Other Load Port Family",
    )
    other_equipment = Equipment(
        id=deterministic_uuid("equipment", other_tenant.code, "LP-99"),
        tenant_id=other_tenant.id,
        line_id=other_line.id,
        family_id=other_family.id,
        code="LP-99",
        name="Other Tenant Load Port",
        status="NORMAL",
    )
    db_session.add(other_tenant)
    db_session.flush()
    db_session.add(other_site)
    db_session.flush()
    db_session.add(other_line)
    db_session.add(other_family)
    db_session.flush()
    db_session.add(other_equipment)
    db_session.commit()

    visible_codes = db_session.scalars(
        select(Equipment.code).where(Equipment.tenant_id == primary_tenant.id).order_by(Equipment.code)
    ).all()
    cross_tenant_match = db_session.scalar(
        select(Equipment).where(Equipment.tenant_id == primary_tenant.id, Equipment.code == "LP-99")
    )

    assert visible_codes == ["LP-01", "LP-02", "LP-03"]
    assert cross_tenant_match is None


def test_audit_event_creation(db_session: Session):
    tenant = _tenant(db_session)
    equipment = db_session.scalar(
        select(Equipment).where(Equipment.tenant_id == tenant.id, Equipment.code == "LP-01")
    )
    assert equipment is not None

    event = AuditEvent(
        id=deterministic_uuid("audit_event", tenant.code, "EQUIPMENT_DETAIL_VIEWED", equipment.code),
        tenant_id=tenant.id,
        event_type="EQUIPMENT_DETAIL_VIEWED",
        resource_type="equipment",
        resource_id=equipment.id,
        severity="INFO",
        payload={"equipment_code": equipment.code},
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.commit()

    events = db_session.scalars(
        select(AuditEvent).where(AuditEvent.tenant_id == tenant.id).order_by(AuditEvent.event_type)
    ).all()
    response = AuditEventListResponse(items=[AuditEventRead.model_validate(item) for item in events])

    assert len(response.items) == 2
    assert any(item.event_type == "EQUIPMENT_DETAIL_VIEWED" for item in response.items)


def _tenant(session: Session) -> Tenant:
    tenant = session.scalar(select(Tenant).where(Tenant.code == "FABMIND_DEMO"))
    assert tenant is not None
    return tenant
