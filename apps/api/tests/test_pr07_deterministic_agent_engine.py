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


def test_clamp_sensor_misalignment_scenario(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-CLAMP-014",
        symptom_summary="Clamp command is issued but clamp done feedback is missing",
        ethercat_state="OP",
        io_snapshot={"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False, "DI_FOUP_PRESENT": True},
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["risk_level"] == "MEDIUM"
    assert len(body["steps"]) == 9
    assert body["hypotheses"][0]["title"] == "Clamp done sensor misalignment or sensor failure"
    assert {"LP-CLAMP-014", "DO_CLAMP_SOL", "DI_CLAMP_DONE"}.issubset(set(body["hypotheses"][0]["evidence_ids"]))
    assert body["evidence"]
    assert body["inspection_plan_items"]
    assert _stored_session(session, session_id).status == "ANALYSIS_READY"
    assert _audit_count(session, "AGENT_ANALYSIS_STARTED") == 1
    assert _audit_count(session, "AGENT_ANALYSIS_COMPLETED") == 1


def test_ethercat_preop_scenario(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    equipment = _equipment(session, "LP-02")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="ECAT-STATE-021",
        symptom_summary="EtherCAT slave 3 remains in PRE_OP",
        ethercat_state="PRE_OP",
        io_snapshot={},
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["safety_result"] == "APPROVAL_REQUIRED_FOR_FORCE_ACTION"
    assert body["risk_level"] == "HIGH"
    assert body["hypotheses"][0]["title"] == "EtherCAT slave communication or state transition problem"
    assert "ETHERCAT_STATE" in body["hypotheses"][0]["evidence_ids"]


def test_foup_door_interlock_scenario(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "admin", "admin-demo-password")
    equipment = _equipment(session, "LP-03")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-DOOR-007",
        symptom_summary="FOUP door closed sensor mismatch in the interlock chain",
        ethercat_state="OP",
        io_snapshot={"DI_DOOR_CLOSED": False, "DI_FOUP_PRESENT": True},
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["risk_level"] == "HIGH"
    assert body["hypotheses"][0]["title"] == "FOUP door sensor or interlock chain issue"
    assert "DI_DOOR_CLOSED" in body["hypotheses"][0]["evidence_ids"]
    assert body["inspection_plan_items"][0]["safety_level"] == "APPROVAL_REQUIRED"


def test_insufficient_evidence_scenario(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-DEMO-006",
        symptom_summary="Intermittent synthetic symptom without enough detail",
        ethercat_state="OP",
        io_snapshot={},
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "INSUFFICIENT_EVIDENCE"
    assert body["hypotheses"] == []
    assert body["evidence"] == []
    assert body["inspection_plan_items"][0]["title"] == "Collect minimum diagnostic evidence"
    assert _stored_session(session, session_id).status == "INSUFFICIENT_EVIDENCE"
    assert _audit_count(session, "AGENT_ANALYSIS_INSUFFICIENT_EVIDENCE") == 1


def test_risky_action_blocked_scenario(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-CLAMP-014",
        symptom_summary="Please bypass the interlock and force output to clear the clamp issue",
        log_excerpt="Operator asked for override of the clamp path",
        ethercat_state="OP",
        io_snapshot={"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
        recent_action="Do not wait for senior review",
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SAFETY_BLOCKED"
    assert body["safety_result"] == "POLICY_BLOCKED_RISKY_ACTION"
    assert body["risk_level"] == "CRITICAL"
    assert body["hypotheses"][0]["evidence_ids"] == ["SAFETY-POLICY-001"]
    assert _stored_session(session, session_id).status == "CLOSED"
    assert _audit_count(session, "AGENT_RISKY_ACTION_BLOCKED") == 1


def test_tenant_isolation_blocks_foreign_session_analysis(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    other_session = _create_other_tenant_session(session)

    response = client.post(f"/api/v1/diagnosis-sessions/{other_session.id}/analyze", headers=_auth_header(token))

    assert response.status_code == 404
    assert _audit_count(session, "DIAGNOSIS_SESSION_ACCESS_DENIED") == 1


def test_unauthenticated_analysis_rejected(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    equipment = _equipment(session, "LP-01")
    token = _login(client, "field", "field-demo-password")
    session_id = _create_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-CLAMP-014",
        symptom_summary="Clamp command is issued but clamp done feedback is missing",
        ethercat_state="OP",
        io_snapshot={"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
    )

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze")

    assert response.status_code == 401


def _create_session(
    client: TestClient,
    token: str,
    equipment_id: uuid.UUID,
    *,
    alarm_code: str,
    symptom_summary: str,
    ethercat_state: str,
    io_snapshot: dict[str, bool],
    log_excerpt: str | None = None,
    recent_action: str | None = None,
) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": alarm_code,
            "symptom_summary": symptom_summary,
            "log_excerpt": log_excerpt or "Synthetic read-only diagnostic log.",
            "ethercat_state": ethercat_state,
            "io_snapshot": io_snapshot,
            "recent_action": recent_action,
            "risk_level": "LOW",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


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


def _stored_session(session: Session, session_id: str) -> DiagnosisSession:
    stored = session.get(DiagnosisSession, uuid.UUID(session_id))
    assert stored is not None
    return stored


def _audit_count(session: Session, event_type: str) -> int:
    return session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.event_type == event_type))


def _create_other_tenant_session(session: Session) -> DiagnosisSession:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR07_OTHER_TENANT"),
        code="PR07_OTHER_TENANT",
        name="PR-07 Other Synthetic Tenant",
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
        username="pr07-other-field",
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
        io_snapshot={"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
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
