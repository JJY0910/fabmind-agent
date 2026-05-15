from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.seed import deterministic_uuid, seed_database
from app.db.session import get_db
from app.main import app
from app.models import AuditEvent, Equipment, EquipmentFamily, Line, Role, Site, Tenant, User


@pytest.fixture()
def client_and_session() -> Generator[tuple[TestClient, Session], None, None]:
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

        def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            yield client, session
        app.dependency_overrides.clear()

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_equipment_list_success(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/equipment", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert [item["code"] for item in body["items"]] == ["LP-01", "LP-02", "LP-03"]
    assert {item["family"] for item in body["items"]} == {"LOAD_PORT_FOUP_CLAMP"}


def test_equipment_detail_success_logs_audit(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    equipment = _equipment(session, "LP-01")

    response = client.get(f"/api/v1/equipment/{equipment.id}", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["equipment"]["code"] == "LP-01"
    assert len(body["alarms"]) == 30
    assert len(body["io_points"]) == 30
    assert len(body["ethercat_devices"]) == 2
    assert body["document_chunks"] == []
    assert _audit_count(session, "EQUIPMENT_DETAIL_VIEWED") == 1


def test_alarms_list_success(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/alarms", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 30
    assert any(item["code"] == "LP-CLAMP-014" for item in body["items"])


def test_io_points_list_success(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "admin", "admin-demo-password")

    response = client.get("/api/v1/io-points", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 60
    assert {item["direction"] for item in body["items"]} == {"DI", "DO"}


def test_ethercat_devices_list_success(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/ethercat-devices", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 6
    assert {item["expected_state"] for item in body["items"]} == {"OP"}


def test_unauthenticated_request_fails(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session

    response = client.get("/api/v1/equipment")

    assert response.status_code == 401


def test_tenant_isolation_blocks_cross_tenant_equipment_detail(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    other_equipment = _create_other_tenant_equipment(session)

    response = client.get(f"/api/v1/equipment/{other_equipment.id}", headers=_auth_header(token))

    assert response.status_code == 404
    assert _audit_count(session, "EQUIPMENT_ACCESS_DENIED") == 1


def test_invalid_role_access_is_blocked(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    user = _create_guest_user(session)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role_code=user.role.code)

    response = client.get("/api/v1/equipment", headers=_auth_header(token))

    assert response.status_code == 403
    assert _audit_count(session, "RBAC_PERMISSION_DENIED") == 1


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _tenant(session: Session) -> Tenant:
    tenant = session.scalar(select(Tenant).where(Tenant.code == "FABMIND_DEMO"))
    assert tenant is not None
    return tenant


def _equipment(session: Session, code: str) -> Equipment:
    tenant = _tenant(session)
    equipment = session.scalar(select(Equipment).where(Equipment.tenant_id == tenant.id, Equipment.code == code))
    assert equipment is not None
    return equipment


def _audit_count(session: Session, event_type: str) -> int:
    return session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.event_type == event_type))


def _create_other_tenant_equipment(session: Session) -> Equipment:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR05_OTHER_TENANT"),
        code="PR05_OTHER_TENANT",
        name="PR-05 Other Synthetic Tenant",
    )
    other_site = Site(
        id=deterministic_uuid("site", other_tenant.code, "SITE-X"),
        tenant_id=other_tenant.id,
        code="SITE-X",
        name="Other Site",
    )
    other_line = Line(
        id=deterministic_uuid("line", other_tenant.code, "LINE-X"),
        tenant_id=other_tenant.id,
        site_id=other_site.id,
        code="LINE-X",
        name="Other Line",
    )
    other_family = EquipmentFamily(
        id=deterministic_uuid("equipment_family", other_tenant.code, "LOAD_PORT_FOUP_CLAMP"),
        tenant_id=other_tenant.id,
        code="LOAD_PORT_FOUP_CLAMP",
        name="Other Load Port Family",
    )
    other_equipment = Equipment(
        id=deterministic_uuid("equipment", other_tenant.code, "LP-X"),
        tenant_id=other_tenant.id,
        line_id=other_line.id,
        family_id=other_family.id,
        code="LP-X",
        name="Other Tenant Load Port",
        status="NORMAL",
    )
    session.add(other_tenant)
    session.flush()
    session.add(other_site)
    session.flush()
    session.add(other_line)
    session.add(other_family)
    session.flush()
    session.add(other_equipment)
    session.commit()
    return other_equipment


def _create_guest_user(session: Session) -> User:
    tenant = _tenant(session)
    role = Role(
        id=deterministic_uuid("role", "READ_ONLY_GUEST"),
        code="READ_ONLY_GUEST",
        name="Read Only Guest",
    )
    user = User(
        id=deterministic_uuid("user", tenant.code, "guest"),
        tenant_id=tenant.id,
        role_id=role.id,
        username="guest",
        display_name="Guest",
        password_hash="unused",
        is_active=True,
    )
    session.add(role)
    session.flush()
    session.add(user)
    session.commit()
    return user

