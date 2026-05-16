from __future__ import annotations

import csv
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AlarmCode,
    AuditEvent,
    Equipment,
    EquipmentFamily,
    EquipmentIncident,
    EthercatDevice,
    IoPoint,
    Line,
    Role,
    Site,
    Tenant,
    User,
)


UUID_NAMESPACE = uuid.UUID("6ca53c06-68e2-5f14-b45a-69f38e0a9c5e")
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SEED_DIR = REPO_ROOT / "db" / "seeds"


@dataclass(frozen=True)
class SeedSummary:
    tenants: int
    roles: int
    users: int
    sites: int
    lines: int
    equipment_families: int
    equipment: int
    alarm_codes: int
    io_points: int
    ethercat_devices: int
    audit_events: int


def deterministic_uuid(*parts: str) -> uuid.UUID:
    return uuid.uuid5(UUID_NAMESPACE, ":".join(parts))


def seed_database(session: Session, seed_dir: Path | None = None) -> SeedSummary:
    source_dir = seed_dir or DEFAULT_SEED_DIR
    core = _read_json(source_dir / "core_seed.json")

    tenant = _seed_tenant(session, core["tenant"])
    roles = _seed_roles(session, core["roles"])
    users = _seed_users(session, tenant, roles, core["users"])
    site = _seed_site(session, tenant, core["site"])
    line = _seed_line(session, tenant, site, core["line"])
    family = _seed_equipment_family(session, tenant, core["equipment_family"])
    equipment = _seed_equipment(session, tenant, line, family, core["equipment"])
    ethercat_devices = _seed_ethercat_devices(session, tenant, equipment, core["ethercat_devices"])
    alarm_codes = _seed_alarm_codes(session, tenant, family, source_dir / "alarm_codes_seed.csv")
    io_points = _seed_io_points(session, tenant, equipment, source_dir / "io_points_seed.csv")
    audit_events = _seed_audit_event(session, tenant, users, core["audit_event"])
    _seed_representative_incident(session, tenant, users, equipment)

    session.commit()

    return SeedSummary(
        tenants=1,
        roles=len(roles),
        users=len(users),
        sites=1,
        lines=1,
        equipment_families=1,
        equipment=len(equipment),
        alarm_codes=alarm_codes,
        io_points=io_points,
        ethercat_devices=ethercat_devices,
        audit_events=audit_events,
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _seed_tenant(session: Session, data: dict[str, str]) -> Tenant:
    tenant = Tenant(
        id=deterministic_uuid("tenant", data["code"]),
        code=data["code"],
        name=data["name"],
    )
    session.merge(tenant)
    session.flush()
    return tenant


def _seed_roles(session: Session, rows: list[dict[str, str]]) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for row in rows:
        role = Role(
            id=deterministic_uuid("role", row["code"]),
            code=row["code"],
            name=row["name"],
        )
        session.merge(role)
        roles[role.code] = role
    session.flush()
    return roles


def _seed_users(session: Session, tenant: Tenant, roles: dict[str, Role], rows: list[dict[str, str]]) -> dict[str, User]:
    users: dict[str, User] = {}
    for row in rows:
        user = User(
            id=deterministic_uuid("user", tenant.code, row["username"]),
            tenant_id=tenant.id,
            role_id=roles[row["role_code"]].id,
            username=row["username"],
            display_name=row["display_name"],
            password_hash=row["password_hash"],
            is_active=True,
        )
        session.merge(user)
        users[user.username] = user
    session.flush()
    return users


def _seed_site(session: Session, tenant: Tenant, data: dict[str, str]) -> Site:
    site = Site(
        id=deterministic_uuid("site", tenant.code, data["code"]),
        tenant_id=tenant.id,
        code=data["code"],
        name=data["name"],
    )
    session.merge(site)
    session.flush()
    return site


def _seed_line(session: Session, tenant: Tenant, site: Site, data: dict[str, str]) -> Line:
    line = Line(
        id=deterministic_uuid("line", tenant.code, data["code"]),
        tenant_id=tenant.id,
        site_id=site.id,
        code=data["code"],
        name=data["name"],
    )
    session.merge(line)
    session.flush()
    return line


def _seed_equipment_family(session: Session, tenant: Tenant, data: dict[str, str]) -> EquipmentFamily:
    family = EquipmentFamily(
        id=deterministic_uuid("equipment_family", tenant.code, data["code"]),
        tenant_id=tenant.id,
        code=data["code"],
        name=data["name"],
    )
    session.merge(family)
    session.flush()
    return family


def _seed_equipment(
    session: Session,
    tenant: Tenant,
    line: Line,
    family: EquipmentFamily,
    rows: list[dict[str, str]],
) -> dict[str, Equipment]:
    equipment_by_code: dict[str, Equipment] = {}
    for row in rows:
        equipment = Equipment(
            id=deterministic_uuid("equipment", tenant.code, row["code"]),
            tenant_id=tenant.id,
            line_id=line.id,
            family_id=family.id,
            code=row["code"],
            name=row["name"],
            vendor=row.get("vendor"),
            model=row.get("model"),
            revision=row.get("revision"),
            status=row.get("status", "NORMAL"),
        )
        session.merge(equipment)
        equipment_by_code[equipment.code] = equipment
    session.flush()
    return equipment_by_code


def _seed_ethercat_devices(
    session: Session,
    tenant: Tenant,
    equipment_by_code: dict[str, Equipment],
    rows: list[dict[str, Any]],
) -> int:
    for row in rows:
        equipment = equipment_by_code[row["equipment_code"]]
        device = EthercatDevice(
            id=deterministic_uuid("ethercat_device", tenant.code, equipment.code, str(row["slave_no"])),
            tenant_id=tenant.id,
            equipment_id=equipment.id,
            slave_no=row["slave_no"],
            name=row["name"],
            expected_state=row["expected_state"],
            vendor_id=row.get("vendor_id"),
            product_code=row.get("product_code"),
        )
        session.merge(device)
    session.flush()
    return len(rows)


def _seed_alarm_codes(session: Session, tenant: Tenant, family: EquipmentFamily, path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            alarm = AlarmCode(
                id=deterministic_uuid("alarm_code", tenant.code, family.code, row["code"]),
                tenant_id=tenant.id,
                equipment_family_id=family.id,
                code=row["code"],
                severity=row["severity"],
                title=row["title"],
                description=row["description"],
                primary_signal=row.get("primary_signal") or None,
                recommended_first_check=row.get("recommended_first_check") or None,
            )
            session.merge(alarm)
            count += 1
    session.flush()
    return count


def _seed_io_points(session: Session, tenant: Tenant, equipment_by_code: dict[str, Equipment], path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            equipment = equipment_by_code[row["equipment_code"]]
            io_point = IoPoint(
                id=deterministic_uuid("io_point", tenant.code, equipment.code, row["code"]),
                tenant_id=tenant.id,
                equipment_id=equipment.id,
                code=row["code"],
                direction=row["direction"],
                signal_type=row["signal_type"],
                description=row["description"],
                normal_state=_to_bool(row.get("normal_state")),
                related_alarm_code=row.get("related_alarm") or None,
            )
            session.merge(io_point)
            count += 1
    session.flush()
    return count


def _seed_audit_event(session: Session, tenant: Tenant, users: dict[str, User], data: dict[str, Any]) -> int:
    actor = users[data["actor_username"]]
    event = AuditEvent(
        id=deterministic_uuid("audit_event", tenant.code, data["event_type"]),
        tenant_id=tenant.id,
        actor_user_id=actor.id,
        event_type=data["event_type"],
        resource_type=data["resource_type"],
        severity=data["severity"],
        payload=data.get("payload"),
    )
    session.merge(event)
    session.flush()
    return 1


def _seed_representative_incident(
    session: Session,
    tenant: Tenant,
    users: dict[str, User],
    equipment: dict[str, Equipment],
) -> None:
    incident = EquipmentIncident(
        id=deterministic_uuid("incident", tenant.code, "LP-01-BASELINE"),
        tenant_id=tenant.id,
        equipment_id=equipment["LP-01"].id,
        case_number="INC-LP-01-BASELINE",
        title="LP-01 FOUP clamp evidence review",
        summary="Representative operational incident for Load Port FOUP clamp and EtherCAT I/O evidence tracking.",
        alarm_code="LP-CLAMP-014",
        severity="MEDIUM",
        status="OPEN",
        owner_user_id=users["field"].id,
        assigned_role="FIELD_ENGINEER",
    )
    session.merge(incident)
    session.flush()


def _to_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    return value.lower() == "true"


def get_seeded_tenant_id(session: Session) -> uuid.UUID:
    return session.scalar(select(Tenant.id).where(Tenant.code == "FABMIND_DEMO"))
