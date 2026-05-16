from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from app.models import AuditEvent, Equipment, EquipmentIncident, Tenant


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


def test_unauthenticated_incident_access_is_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    incident_id = uuid.uuid4()

    assert client.get("/api/v1/incidents").status_code == 401
    assert client.get(f"/api/v1/incidents/{incident_id}").status_code == 401
    assert client.post("/api/v1/incidents", json={}).status_code == 401
    assert client.patch(f"/api/v1/incidents/{incident_id}/status", json={"status": "TRIAGED"}).status_code == 401


def test_get_incidents_returns_representative_first_class_incident(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get(
        "/api/v1/incidents",
        params={"equipment_code": "LP-01", "status": "OPEN", "limit": 1, "offset": 0},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["limit"] == 1
    incident = body["items"][0]
    assert incident["case_number"] == "INC-LP-01-BASELINE"
    assert incident["equipment_code"] == "LP-01"
    assert incident["alarm_code"] == "LP-CLAMP-014"
    assert incident["status"] == "OPEN"

    detail = client.get(f"/api/v1/incidents/{incident['incident_id']}", headers=_auth_header(token))
    assert detail.status_code == 200
    assert detail.json()["case_number"] == "INC-LP-01-BASELINE"


def test_representative_incident_seed_is_idempotent(client_and_session: tuple[TestClient, Session]):
    _client, session = client_and_session

    seed_database(session)

    count = session.scalar(
        select(func.count()).select_from(EquipmentIncident).where(EquipmentIncident.case_number == "INC-LP-01-BASELINE")
    )
    assert count == 1


def test_incident_filters_and_pagination_work(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get(
        "/api/v1/incidents",
        params={"equipment_code": "LP-01", "risk_level": "MEDIUM", "alarm_code": "LP-CLAMP-014", "limit": 10},
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["offset"] == 0
    assert body["items"][0]["risk_level"] == "MEDIUM"


def test_post_incident_creation_succeeds_for_authorized_role_and_stays_read_only(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.post(
        "/api/v1/incidents",
        json={
            "equipment_code": "LP-02",
            "title": "LP-02 EtherCAT status review",
            "summary": "Operational case opened from read-only status evidence.",
            "alarm_code": "ECAT-STATE-021",
            "severity": "HIGH",
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["equipment_code"] == "LP-02"
    assert body["status"] == "OPEN"
    assert "command" not in body
    audit = session.scalar(select(AuditEvent).where(AuditEvent.event_type == "INCIDENT_CREATED"))
    assert audit is not None


def test_alarm_event_ingestion_links_to_single_active_incident(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    for source_event_id in ("ALM-PR24-001", "ALM-PR24-002"):
        response = client.post(
            "/api/v1/equipment-data/alarm-events",
            json={
                "equipment_code": "LP-03",
                "source_event_id": source_event_id,
                "alarm_code": "LP-CLAMP-014",
                "alarm_name": "Clamp done feedback missing",
                "severity": "HIGH",
                "event_status": "ACTIVE",
                "occurred_at": "2026-05-17T09:00:00Z",
                "source_system": "fabmind-readonly-adapter",
                "raw_payload": {"source": "alarm_stream"},
            },
            headers=_auth_header(token),
        )
        assert response.status_code == 201

    incidents = session.scalars(
        select(EquipmentIncident).where(
            EquipmentIncident.equipment_id == _equipment(session, "LP-03").id,
            EquipmentIncident.alarm_code == "LP-CLAMP-014",
        )
    ).all()
    assert len(incidents) == 1
    assert incidents[0].primary_alarm_event_id is not None


def test_alarm_event_after_closed_incident_creates_new_open_incident(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    senior_token = _login(client, "senior", "senior-demo-password")
    incident_id = _create_incident(client, senior_token, "LP-03")
    for target_status in ("TRIAGED", "CHECKLIST_IN_PROGRESS", "REPORT_SUBMITTED", "APPROVED", "CLOSED"):
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": target_status},
            headers=_auth_header(senior_token),
        )
        assert response.status_code == 200

    alarm_response = client.post(
        "/api/v1/equipment-data/alarm-events",
        json={
            "equipment_code": "LP-03",
            "source_event_id": "ALM-AFTER-CLOSED",
            "alarm_code": "LP-CLAMP-014",
            "alarm_name": "Clamp done feedback missing",
            "severity": "HIGH",
            "event_status": "ACTIVE",
            "occurred_at": "2026-05-17T10:00:00Z",
            "source_system": "fabmind-readonly-adapter",
            "raw_payload": {"source": "alarm_stream"},
        },
        headers=_auth_header(senior_token),
    )
    assert alarm_response.status_code == 201

    incidents = session.scalars(
        select(EquipmentIncident).where(
            EquipmentIncident.equipment_id == _equipment(session, "LP-03").id,
            EquipmentIncident.alarm_code == "LP-CLAMP-014",
        )
    ).all()
    assert len(incidents) == 2
    assert {incident.status for incident in incidents} == {"CLOSED", "OPEN"}


def test_diagnosis_session_links_existing_active_incident_without_duplicate(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")

    session_id = _create_diagnosis_session(client, token, equipment.id)

    incidents = session.scalars(
        select(EquipmentIncident).where(
            EquipmentIncident.equipment_id == equipment.id,
            EquipmentIncident.alarm_code == "LP-CLAMP-014",
            EquipmentIncident.status != "CLOSED",
            EquipmentIncident.status != "CANCELLED",
        )
    ).all()
    assert len(incidents) == 1
    assert str(incidents[0].diagnosis_session_id) == session_id
    assert incidents[0].case_number == "INC-LP-01-BASELINE"


def test_field_user_cannot_close_or_approve_incident(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    incident_id = _create_incident(client, token, "LP-02")

    response = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "CLOSED"},
        headers=_auth_header(token),
    )

    assert response.status_code == 403
    audit = session.scalar(select(AuditEvent).where(AuditEvent.event_type == "INCIDENT_UPDATE_DENIED"))
    assert audit is not None


def test_senior_can_transition_and_close_incident(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    incident_id = _create_incident(client, field_token, "LP-02")

    for target_status in ("TRIAGED", "CHECKLIST_IN_PROGRESS", "REPORT_SUBMITTED", "APPROVED", "CLOSED"):
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": target_status},
            headers=_auth_header(senior_token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == target_status

    detail = client.get(f"/api/v1/incidents/{incident_id}", headers=_auth_header(senior_token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["triaged_at"] is not None
    assert body["checklist_started_at"] is not None
    assert body["report_submitted_at"] is not None
    assert body["approved_at"] is not None
    assert body["closed_at"] is not None


def test_senior_can_cancel_open_incident(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    incident_id = _create_incident(client, field_token, "LP-02")

    response = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "CANCELLED"},
        headers=_auth_header(senior_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_invalid_status_transition_is_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    incident_id = _create_incident(client, field_token, "LP-02")

    response = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "APPROVED"},
        headers=_auth_header(senior_token),
    )

    assert response.status_code == 400


def test_incident_links_attach_diagnosis_checklist_report_and_approval(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200
    approved = client.post(f"/api/v1/report-drafts/{report['id']}/approve", headers=_auth_header(senior_token))
    assert approved.status_code == 200
    approval_id = approved.json()["approvals"][0]["id"]
    checklist_run_id = approved.json()["checklist_run_id"]

    incident = session.scalar(select(EquipmentIncident).where(EquipmentIncident.diagnosis_session_id == uuid.UUID(session_id)))
    assert incident is not None

    response = client.patch(
        f"/api/v1/incidents/{incident.id}/links",
        json={
            "diagnosis_session_id": session_id,
            "checklist_run_id": checklist_run_id,
            "report_draft_id": report["id"],
            "approval_id": approval_id,
        },
        headers=_auth_header(field_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis_session_id"] == session_id
    assert body["linked_checklist_run_id"] == checklist_run_id
    assert body["linked_report_draft_id"] == report["id"]
    assert body["linked_approval_id"] == approval_id
    audit_types = {
        item
        for item in session.scalars(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type.in_(
                    [
                        "INCIDENT_LINKED_TO_DIAGNOSIS",
                        "INCIDENT_LINKED_TO_CHECKLIST",
                        "INCIDENT_LINKED_TO_REPORT",
                    ]
                )
            )
        ).all()
    }
    assert audit_types == {
        "INCIDENT_LINKED_TO_DIAGNOSIS",
        "INCIDENT_LINKED_TO_CHECKLIST",
        "INCIDENT_LINKED_TO_REPORT",
    }


def test_incident_linking_validates_missing_resources_and_audits_diagnosis_link(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-02")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    incident_id = _create_incident(client, token, "LP-02")

    missing_link = client.patch(
        f"/api/v1/incidents/{incident_id}/links",
        json={"checklist_run_id": str(uuid.uuid4())},
        headers=_auth_header(token),
    )
    assert missing_link.status_code == 404

    linked = client.patch(
        f"/api/v1/incidents/{incident_id}/links",
        json={"diagnosis_session_id": session_id},
        headers=_auth_header(token),
    )
    assert linked.status_code == 200
    assert linked.json()["diagnosis_session_id"] == session_id
    audit = session.scalar(select(AuditEvent).where(AuditEvent.event_type == "INCIDENT_LINKED_TO_DIAGNOSIS"))
    assert audit is not None


def test_openapi_contract_contains_incident_lifecycle_paths_and_no_unsafe_equipment_paths():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    assert _path_methods(text, "/api/v1/incidents") == {"get", "post"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}") == {"get"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}/status") == {"patch"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}/links") == {"patch"}
    for path in _api_paths(text):
        lowered = path.lower()
        for unsafe_fragment in ("command", "control", "force", "override", "bypass", "servo", "reset", "motion"):
            assert unsafe_fragment not in lowered


def _create_incident(client: TestClient, token: str, equipment_code: str) -> str:
    response = client.post(
        "/api/v1/incidents",
        json={
            "equipment_code": equipment_code,
            "title": f"{equipment_code} operational case",
            "summary": "Read-only evidence review case.",
            "alarm_code": "LP-CLAMP-014",
            "severity": "HIGH",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["incident_id"]


def _create_report_ready_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    analysis = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert analysis.status_code == 200
    checklist = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))
    assert checklist.status_code == 201
    item_id = checklist.json()["items"][0]["id"]
    completed = client.patch(
        f"/api/v1/checklist-runs/{checklist.json()['id']}/items/{item_id}",
        json={"status": "DONE", "field_note": "Read-only inspection completed."},
        headers=_auth_header(token),
    )
    assert completed.status_code == 200
    return session_id


def _create_diagnosis_session(client: TestClient, token: str, equipment_id: uuid.UUID) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": "LP-CLAMP-014",
            "symptom_summary": "Clamp command is issued but clamp done feedback is missing",
            "log_excerpt": "Synthetic read-only diagnostic log.",
            "ethercat_state": "OP",
            "io_snapshot": {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Read-only inspection note.",
            "risk_level": "HIGH",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


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


def _path_methods(text: str, path: str) -> set[str]:
    lines = text.splitlines()
    try:
        start = lines.index(f"  {path}:")
    except ValueError as exc:
        raise AssertionError(f"Missing OpenAPI path: {path}") from exc

    methods: set[str] = set()
    for line in lines[start + 1 :]:
        if line.startswith("  /") or line.startswith("components:"):
            break
        if line.startswith("    ") and not line.startswith("      "):
            method = line.strip().rstrip(":")
            if method in {"get", "post", "put", "patch", "delete"}:
                methods.add(method)
    return methods


def _api_paths(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("/api/v1/") and stripped.endswith(":"):
            paths.append(stripped.rstrip(":"))
    return paths
