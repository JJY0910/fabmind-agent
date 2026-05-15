from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed import deterministic_uuid, seed_database
from app.db.session import get_db
from app.main import app
from app.models import AuditEvent, DiagnosisSession, Equipment, EquipmentFamily, Line, Role, Site, Tenant, User


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


def test_create_diagnosis_session_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")

    response = client.post("/api/v1/diagnosis-sessions", json=_create_payload(equipment.id), headers=_auth_header(token))

    assert response.status_code == 201
    body = response.json()
    assert body["equipment_id"] == str(equipment.id)
    assert body["created_by_user_id"]
    assert body["alarm_code"] == "LP-CLAMP-014"
    assert body["symptom_summary"] == "Clamp command issued but clamp done signal is not detected"
    assert body["ethercat_state"] == "OP"
    assert body["status"] == "CREATED"
    assert body["risk_level"] == "MEDIUM"
    assert _audit_count(session, "DIAGNOSIS_SESSION_CREATED") == 1


def test_list_diagnosis_sessions_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    equipment = _equipment(session, "LP-01")
    created = client.post(
        "/api/v1/diagnosis-sessions",
        json=_create_payload(equipment.id),
        headers=_auth_header(token),
    )
    assert created.status_code == 201

    response = client.get("/api/v1/diagnosis-sessions", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == created.json()["id"]


def test_detail_diagnosis_session_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "admin", "admin-demo-password")
    equipment = _equipment(session, "LP-01")
    created = client.post(
        "/api/v1/diagnosis-sessions",
        json=_create_payload(equipment.id),
        headers=_auth_header(token),
    )
    assert created.status_code == 201

    response = client.get(f"/api/v1/diagnosis-sessions/{created.json()['id']}", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created.json()["id"]
    assert body["io_snapshot"] == {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False, "DI_FOUP_PRESENT": True}
    assert _audit_count(session, "DIAGNOSIS_SESSION_VIEWED") == 1


def test_unknown_equipment_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.post(
        "/api/v1/diagnosis-sessions",
        json=_create_payload(uuid.uuid4()),
        headers=_auth_header(token),
    )

    assert response.status_code == 422


def test_unknown_alarm_rejected(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    payload = _create_payload(equipment.id)
    payload["alarm_code"] = "UNKNOWN-ALARM"

    response = client.post("/api/v1/diagnosis-sessions", json=payload, headers=_auth_header(token))

    assert response.status_code == 422


def test_unauthenticated_request_rejected(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    equipment = _equipment(session, "LP-01")

    response = client.post("/api/v1/diagnosis-sessions", json=_create_payload(equipment.id))

    assert response.status_code == 401


def test_tenant_isolation_blocks_foreign_session_detail(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    other_session = _create_other_tenant_session(session)

    response = client.get(f"/api/v1/diagnosis-sessions/{other_session.id}", headers=_auth_header(token))

    assert response.status_code == 404
    assert _audit_count(session, "DIAGNOSIS_SESSION_ACCESS_DENIED") == 1


def _create_payload(equipment_id: uuid.UUID) -> dict[str, object]:
    return {
        "equipment_id": str(equipment_id),
        "alarm_code": "LP-CLAMP-014",
        "symptom_summary": "Clamp command issued but clamp done signal is not detected",
        "log_excerpt": "Synthetic demo log excerpt for Load Port clamp troubleshooting.",
        "ethercat_state": "OP",
        "io_snapshot": {
            "DO_CLAMP_SOL": True,
            "DI_CLAMP_DONE": False,
            "DI_FOUP_PRESENT": True,
        },
        "recent_action": "Synthetic sensor bracket inspection note.",
        "risk_level": "MEDIUM",
    }


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


def _create_other_tenant_session(session: Session) -> DiagnosisSession:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR06_OTHER_TENANT"),
        code="PR06_OTHER_TENANT",
        name="PR-06 Other Synthetic Tenant",
    )
    other_site = Site(
        id=deterministic_uuid("site", other_tenant.code, "SITE-Z"),
        tenant_id=other_tenant.id,
        code="SITE-Z",
        name="Other Site",
    )
    other_line = Line(
        id=deterministic_uuid("line", other_tenant.code, "LINE-Z"),
        tenant_id=other_tenant.id,
        site_id=other_site.id,
        code="LINE-Z",
        name="Other Line",
    )
    other_family = EquipmentFamily(
        id=deterministic_uuid("equipment_family", other_tenant.code, "LOAD_PORT_FOUP_CLAMP"),
        tenant_id=other_tenant.id,
        code="LOAD_PORT_FOUP_CLAMP",
        name="Other Load Port Family",
    )
    other_equipment = Equipment(
        id=deterministic_uuid("equipment", other_tenant.code, "LP-Z"),
        tenant_id=other_tenant.id,
        line_id=other_line.id,
        family_id=other_family.id,
        code="LP-Z",
        name="Other Tenant Load Port",
        status="NORMAL",
    )
    role = session.scalar(select(Role).where(Role.code == "FIELD_ENGINEER"))
    assert role is not None
    other_user = User(
        id=deterministic_uuid("user", other_tenant.code, "field"),
        tenant_id=other_tenant.id,
        role_id=role.id,
        username="other-field",
        display_name="Other Field",
        password_hash="unused",
        is_active=True,
    )
    other_session = DiagnosisSession(
        id=deterministic_uuid("diagnosis_session", other_tenant.code, "foreign-session"),
        tenant_id=other_tenant.id,
        equipment_id=other_equipment.id,
        created_by_user_id=other_user.id,
        alarm_code="LP-CLAMP-014",
        symptom_summary="Foreign tenant synthetic symptom",
        io_snapshot={},
        status="CREATED",
        risk_level="LOW",
    )
    session.add(other_tenant)
    session.flush()
    session.add(other_site)
    session.flush()
    session.add(other_line)
    session.add(other_family)
    session.flush()
    session.add(other_equipment)
    session.add(other_user)
    session.flush()
    session.add(other_session)
    session.commit()
    return other_session

