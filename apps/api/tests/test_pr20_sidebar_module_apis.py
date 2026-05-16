from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from app.models import Equipment, Tenant


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


def test_equipment_registry_list_supports_pagination_and_operational_fields(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/equipment", params={"limit": 2, "offset": 0}, headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [item["equipment_code"] for item in body["items"]] == ["LP-01", "LP-02"]
    first = body["items"][0]
    assert first["equipment_id"] == first["id"]
    assert first["equipment_name"] == "Load Port 01"
    assert first["equipment_type"] == "Load Port / FOUP Clamp"
    assert first["subsystem"] == "FOUP Clamp / EtherCAT I/O"
    assert first["location"] == "SITE-A / LINE-LP-A"
    assert first["operational_status"] == "NORMAL"


def test_equipment_registry_filter_by_status(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/equipment", params={"status": "WARNING"}, headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["equipment_code"] == "LP-02"


def test_active_incidents_list_and_detail_derive_from_diagnosis_sessions(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id, risk_level="HIGH")

    response = client.get(
        "/api/v1/incidents",
        params={"equipment_code": "LP-01", "risk_level": "HIGH"},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    incident = body["items"][0]
    assert incident["incident_id"] == session_id
    assert incident["equipment_code"] == "LP-01"
    assert incident["alarm_code"] == "LP-CLAMP-014"
    assert incident["risk_level"] == "HIGH"
    assert incident["status"] == "CREATED"
    assert incident["linked_checklist_run_id"] is None
    assert incident["linked_report_draft_id"] is None

    detail = client.get(f"/api/v1/incidents/{session_id}", headers=_auth_header(token))
    assert detail.status_code == 200
    assert detail.json()["diagnosis_session_id"] == session_id


def test_checklist_run_list_filters_and_item_counts(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_analyzed_session(client, session, token)
    checklist = _create_checklist_run(client, token, session_id)

    response = client.get(
        "/api/v1/checklist-runs",
        params={"status": "CREATED", "diagnosis_session_id": session_id},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["checklist_run_id"] == checklist["id"]
    assert item["diagnosis_session_id"] == session_id
    assert item["equipment_code"] == "LP-01"
    assert item["total_items"] == 1
    assert item["completed_items"] == 0
    assert item["failed_items"] == 0
    assert item["pending_items"] == 1


def test_report_draft_list_and_approval_queue_use_real_report_records(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200

    reports = client.get(
        "/api/v1/report-drafts",
        params={"status": "SUBMITTED", "equipment_code": "LP-01"},
        headers=_auth_header(field_token),
    )
    assert reports.status_code == 200
    report_body = reports.json()
    assert report_body["total"] == 1
    assert report_body["items"][0]["report_draft_id"] == report["id"]
    assert report_body["items"][0]["status"] == "SUBMITTED"
    assert report_body["items"][0]["submitted_at"]

    approvals = client.get(
        "/api/v1/approvals",
        params={"status": "PENDING_REVIEW"},
        headers=_auth_header(senior_token),
    )
    assert approvals.status_code == 200
    approval_body = approvals.json()
    assert approval_body["total"] == 1
    assert approval_body["items"][0]["report_draft_id"] == report["id"]
    assert approval_body["items"][0]["approval_status"] == "PENDING_REVIEW"
    assert approval_body["items"][0]["reviewer_role"] == "SENIOR_ENGINEER_OR_ADMIN"


def test_field_user_cannot_read_approval_queue(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/approvals", headers=_auth_header(token))

    assert response.status_code == 403


def test_system_safety_settings_are_read_only_and_safe(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "admin", "admin-demo-password")

    response = client.get("/api/v1/system/safety-settings", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["external_ai_enabled"] is False
    assert body["equipment_control_enabled"] is False
    assert body["interlock_bypass_allowed"] is False
    assert body["output_forcing_allowed"] is False
    assert body["human_approval_required"] is True
    assert body["audit_logging_enabled"] is True
    assert body["deterministic_engine_enabled"] is True
    assert body["allowed_equipment_scope"] == ["Load Port", "FOUP Clamp", "EtherCAT I/O"]
    assert body["policy_version"] == "PR-20-read-only-safety-boundary-v1"

    mutation = client.post("/api/v1/system/safety-settings", json={}, headers=_auth_header(token))
    assert mutation.status_code == 405


def test_new_sidebar_module_endpoints_require_authentication(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session

    response = client.get("/api/v1/incidents")

    assert response.status_code == 401


def test_openapi_contract_contains_implemented_pr20_paths():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    for path in (
        "/api/v1/incidents:",
        "/api/v1/incidents/{incident_id}:",
        "/api/v1/checklist-runs:",
        "/api/v1/report-drafts:",
        "/api/v1/approvals:",
        "/api/v1/system/safety-settings:",
    ):
        assert path in text


def _create_analyzed_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    return session_id


def _create_report_ready_session(client: TestClient, session: Session, token: str) -> str:
    session_id = _create_analyzed_session(client, session, token)
    checklist = _create_checklist_run(client, token, session_id)
    item_id = checklist["items"][0]["id"]
    response = client.patch(
        f"/api/v1/checklist-runs/{checklist['id']}/items/{item_id}",
        json={"status": "DONE", "field_note": "Read-only inspection completed."},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    return session_id


def _create_diagnosis_session(
    client: TestClient,
    token: str,
    equipment_id: uuid.UUID,
    *,
    risk_level: str = "LOW",
) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": "LP-CLAMP-014",
            "symptom_summary": "Clamp command is issued but clamp done feedback is missing",
            "log_excerpt": "Synthetic read-only diagnostic log.",
            "ethercat_state": "OP",
            "io_snapshot": {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Synthetic inspection note.",
            "risk_level": risk_level,
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_checklist_run(client: TestClient, token: str, session_id: str) -> dict[str, object]:
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))
    assert response.status_code == 201
    return response.json()


def _create_report_draft(client: TestClient, token: str, session_id: str) -> dict[str, object]:
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts", headers=_auth_header(token))
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
