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
from app.models import (
    AgentRun,
    AuditEvent,
    ChecklistItem,
    ChecklistRun,
    DiagnosisSession,
    Equipment,
    EquipmentFamily,
    InspectionPlanItem,
    Line,
    Role,
    Site,
    Tenant,
    User,
)


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


def test_create_checklist_run_from_analyzed_diagnosis_session(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_analyzed_session(client, session, token)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))

    assert response.status_code == 201
    body = response.json()
    assert body["diagnosis_session_id"] == session_id
    assert body["status"] == "CREATED"
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "TODO"
    assert body["items"][0]["source_inspection_plan_item_id"]
    assert _audit_count(session, "CHECKLIST_RUN_CREATED") == 1


def test_create_checklist_run_fails_if_no_analysis_exists(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))

    assert response.status_code == 400
    assert "No completed agent analysis" in response.json()["detail"]


def test_get_checklist_run_detail(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    session_id = _create_analyzed_session(client, session, token)
    created = _create_checklist_run(client, token, session_id)

    response = client.get(f"/api/v1/checklist-runs/{created['id']}", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["items"][0]["title"] == created["items"][0]["title"]


def test_update_checklist_item_to_done(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_analyzed_session(client, session, token)
    checklist_run = _create_checklist_run(client, token, session_id)
    item_id = checklist_run["items"][0]["id"]

    response = client.patch(
        f"/api/v1/checklist-runs/{checklist_run['id']}/items/{item_id}",
        json={"status": "DONE", "field_note": "Sensor LED was on after bracket inspection."},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["items"][0]["status"] == "DONE"
    assert body["items"][0]["field_note"] == "Sensor LED was on after bracket inspection."
    assert body["items"][0]["completed_by_user_id"]
    assert body["items"][0]["completed_at"]
    assert _audit_count(session, "CHECKLIST_ITEM_STATUS_UPDATED") == 1
    assert _audit_count(session, "CHECKLIST_ITEM_COMPLETED") == 1


def test_update_checklist_item_to_blocked_with_field_note(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    session_id = _create_analyzed_session(client, session, token)
    checklist_run = _create_checklist_run(client, token, session_id)
    item_id = checklist_run["items"][0]["id"]

    response = client.patch(
        f"/api/v1/checklist-runs/{checklist_run['id']}/items/{item_id}",
        json={"status": "BLOCKED", "field_note": "Cannot inspect safely until senior review."},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "BLOCKED"
    assert body["items"][0]["status"] == "BLOCKED"
    assert body["items"][0]["field_note"] == "Cannot inspect safely until senior review."
    assert _audit_count(session, "CHECKLIST_ITEM_BLOCKED") == 1


def test_run_status_becomes_completed_when_all_items_done_or_skipped(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "admin", "admin-demo-password")
    session_id = _create_multi_item_analyzed_session(client, session, token)
    checklist_run = _create_checklist_run(client, token, session_id)
    assert len(checklist_run["items"]) == 2

    first = client.patch(
        f"/api/v1/checklist-runs/{checklist_run['id']}/items/{checklist_run['items'][0]['id']}",
        json={"status": "DONE"},
        headers=_auth_header(token),
    )
    assert first.status_code == 200
    second = client.patch(
        f"/api/v1/checklist-runs/{checklist_run['id']}/items/{checklist_run['items'][1]['id']}",
        json={"status": "SKIPPED", "field_note": "Duplicate read-only evidence already captured."},
        headers=_auth_header(token),
    )

    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "COMPLETED"
    assert {item["status"] for item in body["items"]} == {"DONE", "SKIPPED"}


def test_run_status_becomes_blocked_when_any_item_is_blocked(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "admin", "admin-demo-password")
    session_id = _create_multi_item_analyzed_session(client, session, token)
    checklist_run = _create_checklist_run(client, token, session_id)

    response = client.patch(
        f"/api/v1/checklist-runs/{checklist_run['id']}/items/{checklist_run['items'][1]['id']}",
        json={"status": "BLOCKED", "field_note": "Interlock inspection requires senior approval."},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"


def test_unauthenticated_request_rejected(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_analyzed_session(client, session, token)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs")

    assert response.status_code == 401


def test_tenant_isolation_blocks_foreign_checklist_run(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    other_run = _create_other_tenant_checklist_run(session)

    response = client.get(f"/api/v1/checklist-runs/{other_run.id}", headers=_auth_header(token))

    assert response.status_code == 404
    assert _audit_count(session, "CHECKLIST_RUN_ACCESS_DENIED") == 1


def _create_analyzed_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    return session_id


def _create_multi_item_analyzed_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-03")
    session_id = _create_diagnosis_session(
        client,
        token,
        equipment.id,
        alarm_code="LP-DOOR-007",
        symptom_summary="FOUP door interlock chain mismatch while EtherCAT slave is PRE_OP",
        ethercat_state="PRE_OP",
        io_snapshot={"DI_DOOR_CLOSED": False, "DI_FOUP_PRESENT": True},
    )
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert response.status_code == 200
    assert len(response.json()["inspection_plan_items"]) == 2
    return session_id


def _create_diagnosis_session(
    client: TestClient,
    token: str,
    equipment_id: uuid.UUID,
    *,
    alarm_code: str = "LP-CLAMP-014",
    symptom_summary: str = "Clamp command is issued but clamp done feedback is missing",
    ethercat_state: str = "OP",
    io_snapshot: dict[str, bool] | None = None,
) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": alarm_code,
            "symptom_summary": symptom_summary,
            "log_excerpt": "Synthetic read-only diagnostic log.",
            "ethercat_state": ethercat_state,
            "io_snapshot": io_snapshot or {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Synthetic inspection note.",
            "risk_level": "LOW",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_checklist_run(client: TestClient, token: str, session_id: str) -> dict[str, object]:
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))
    assert response.status_code == 201
    return response.json()


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


def _create_other_tenant_checklist_run(session: Session) -> ChecklistRun:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR09_OTHER_TENANT"),
        code="PR09_OTHER_TENANT",
        name="PR-09 Other Synthetic Tenant",
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
        username="pr09-other-field",
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
        status="ANALYSIS_READY",
        risk_level="MEDIUM",
    )
    other_agent_run = AgentRun(
        id=deterministic_uuid("agent_run", other_tenant.code, "foreign-run"),
        tenant_id=other_tenant.id,
        session_id=other_session.id,
        status="COMPLETED",
        mode="DETERMINISTIC",
        safety_result="SAFE_READ_ONLY",
    )
    other_plan_item = InspectionPlanItem(
        id=deterministic_uuid("inspection_plan_item", other_tenant.code, "foreign-item"),
        tenant_id=other_tenant.id,
        agent_run_id=other_agent_run.id,
        item_order=1,
        title="Foreign checklist source",
        instruction="Synthetic foreign tenant instruction.",
        expected_observation="Synthetic observation.",
        safety_level="NORMAL",
        evidence_codes=[],
    )
    other_run = ChecklistRun(
        id=deterministic_uuid("checklist_run", other_tenant.code, "foreign-run"),
        tenant_id=other_tenant.id,
        diagnosis_session_id=other_session.id,
        agent_run_id=other_agent_run.id,
        created_by_user_id=other_user.id,
        status="CREATED",
    )
    other_item = ChecklistItem(
        id=deterministic_uuid("checklist_item", other_tenant.code, "foreign-item"),
        tenant_id=other_tenant.id,
        checklist_run_id=other_run.id,
        source_inspection_plan_item_id=other_plan_item.id,
        item_order=1,
        title="Foreign checklist item",
        description="Synthetic foreign tenant checklist item.",
        expected_result="Synthetic expected result.",
        status="TODO",
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
    session.add(other_agent_run)
    session.flush()
    session.add(other_plan_item)
    session.flush()
    session.add(other_run)
    session.flush()
    session.add(other_item)
    session.commit()
    return other_run
