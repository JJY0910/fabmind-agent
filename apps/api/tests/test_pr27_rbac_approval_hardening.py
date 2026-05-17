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
from app.models import AuditEvent, Equipment, EquipmentIncident


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


def test_auth_me_returns_current_user_role(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    response = client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "senior"
    assert body["display_name"]
    assert body["role"] == "SENIOR_ENGINEER"
    assert body["tenant_id"]


def test_field_user_cannot_approve_or_reject_report_and_denials_are_audited(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    report = _create_submitted_report(client, session, field_token)

    approve = client.post(f"/api/v1/report-drafts/{report['id']}/approve", headers=_auth_header(field_token))
    reject = client.post(
        f"/api/v1/report-drafts/{report['id']}/reject",
        json={"comment": "Senior/admin review required before final decision."},
        headers=_auth_header(field_token),
    )

    assert approve.status_code == 403
    assert reject.status_code == 403
    denial_events = session.scalars(
        select(AuditEvent)
        .where(AuditEvent.event_type == "RBAC_PERMISSION_DENIED")
        .order_by(AuditEvent.created_at.asc())
    ).all()
    assert len(denial_events) == 2
    for event in denial_events:
        assert event.actor_user_id is not None
        assert event.payload["role"] == "FIELD_ENGINEER"
        assert event.payload["path_params"]["report_draft_id"] == report["id"]
    assert denial_events[0].payload["path"].endswith("/approve")
    assert denial_events[1].payload["path"].endswith("/reject")


def test_senior_can_approve_and_reject_submitted_reports(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    report_to_approve = _create_submitted_report(client, session, field_token)
    report_to_reject = _create_submitted_report(client, session, field_token)

    approve = client.post(
        f"/api/v1/report-drafts/{report_to_approve['id']}/approve",
        json={"comment": "Evidence and checklist trail reviewed."},
        headers=_auth_header(senior_token),
    )
    reject = client.post(
        f"/api/v1/report-drafts/{report_to_reject['id']}/reject",
        json={"comment": "Add clearer inspection evidence before final approval."},
        headers=_auth_header(senior_token),
    )

    assert approve.status_code == 200
    assert approve.json()["status"] == "APPROVED"
    assert reject.status_code == 200
    assert reject.json()["status"] == "REJECTED"
    assert _audit_count(session, "REPORT_DRAFT_APPROVED") == 1
    assert _audit_count(session, "REPORT_DRAFT_REJECTED") == 1


def test_admin_can_approve_and_reject_submitted_reports(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    admin_token = _login(client, "admin", "admin-demo-password")
    report_to_approve = _create_submitted_report(client, _session, field_token)
    report_to_reject = _create_submitted_report(client, _session, field_token)

    approve = client.post(f"/api/v1/report-drafts/{report_to_approve['id']}/approve", headers=_auth_header(admin_token))
    reject = client.post(
        f"/api/v1/report-drafts/{report_to_reject['id']}/reject",
        json={"comment": "Admin review requested additional evidence."},
        headers=_auth_header(admin_token),
    )

    assert approve.status_code == 200
    assert approve.json()["status"] == "APPROVED"
    assert reject.status_code == 200
    assert reject.json()["status"] == "REJECTED"


def test_unauthenticated_protected_actions_are_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    report_id = uuid.uuid4()
    incident_id = uuid.uuid4()

    assert client.post(f"/api/v1/report-drafts/{report_id}/approve").status_code == 401
    assert client.post(f"/api/v1/report-drafts/{report_id}/reject", json={"comment": "Missing auth"}).status_code == 401
    assert client.patch(f"/api/v1/incidents/{incident_id}/status", json={"status": "CLOSED"}).status_code == 401


def test_field_user_cannot_perform_senior_only_incident_transitions_and_denials_are_audited(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    incident_id = _create_incident(client, field_token, "LP-02")

    for target_status in ("APPROVED", "CLOSED", "CANCELLED"):
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": target_status},
            headers=_auth_header(field_token),
        )
        assert response.status_code == 403

    events = session.scalars(
        select(AuditEvent)
        .where(AuditEvent.event_type == "INCIDENT_UPDATE_DENIED")
        .order_by(AuditEvent.created_at.asc())
    ).all()
    assert {event.payload["target_status"] for event in events} == {"APPROVED", "CLOSED", "CANCELLED"}
    for event in events:
        assert str(event.resource_id) == incident_id
        assert event.payload["role"] == "FIELD_ENGINEER"
        assert event.payload["current_status"] == "OPEN"


def test_senior_and_admin_can_complete_senior_incident_transitions(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    admin_token = _login(client, "admin", "admin-demo-password")
    incident_id = _create_incident(client, field_token, "LP-03")

    for target_status in ("TRIAGED", "CHECKLIST_IN_PROGRESS", "REPORT_SUBMITTED", "APPROVED"):
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": target_status},
            headers=_auth_header(senior_token),
        )
        assert response.status_code == 200
        assert response.json()["status"] == target_status

    close = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "CLOSED"},
        headers=_auth_header(admin_token),
    )

    assert close.status_code == 200
    assert close.json()["status"] == "CLOSED"


def test_openapi_keeps_auth_and_approval_paths_without_equipment_control_paths():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    assert "/api/v1/auth/me:" in text
    assert "/api/v1/report-drafts/{report_draft_id}/approve:" in text
    assert "/api/v1/report-drafts/{report_draft_id}/reject:" in text
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("/api/v1/"):
            continue
        path = stripped.rstrip(":").lower()
        for unsafe_fragment in ("command", "control", "force", "override", "bypass", "servo", "reset", "motion"):
            assert unsafe_fragment not in path


def _create_submitted_report(client: TestClient, session: Session, field_token: str) -> dict[str, object]:
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"
    return submitted.json()


def _create_report_ready_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    analyze = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert analyze.status_code == 200
    checklist = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))
    assert checklist.status_code == 201
    item_id = checklist.json()["items"][0]["id"]
    completed = client.patch(
        f"/api/v1/checklist-runs/{checklist.json()['id']}/items/{item_id}",
        json={"status": "DONE", "field_note": "Read-only inspection completed."},
        headers=_auth_header(token),
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"
    return session_id


def _create_diagnosis_session(client: TestClient, token: str, equipment_id: uuid.UUID) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": "LP-CLAMP-014",
            "symptom_summary": "Clamp request is observed but clamp done feedback is missing",
            "log_excerpt": "Synthetic read-only diagnostic log.",
            "ethercat_state": "OP",
            "io_snapshot": {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Read-only inspection note.",
            "risk_level": "LOW",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_report_draft(client: TestClient, token: str, session_id: str) -> dict[str, object]:
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts", headers=_auth_header(token))
    assert response.status_code == 201
    return response.json()


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


def _equipment(session: Session, code: str) -> Equipment:
    equipment = session.scalar(select(Equipment).where(Equipment.code == code))
    assert equipment is not None
    return equipment


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _audit_count(session: Session, event_type: str) -> int:
    return session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.event_type == event_type))
