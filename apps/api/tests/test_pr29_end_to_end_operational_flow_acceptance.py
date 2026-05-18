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
from app.models import AuditEvent, Equipment, EquipmentIncident, ReportDraft


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


def test_alarm_to_incident_to_report_approval_flow(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")

    alarm = client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-01", source_event_id="ALM-PR29-E2E"),
        headers=_auth_header(senior_token),
    )
    assert alarm.status_code == 201
    alarm_body = alarm.json()
    assert alarm_body["equipment_code"] == "LP-01"
    assert alarm_body["alarm_code"] == "LP-CLAMP-014"

    incident = _incident_for(client, field_token, equipment_code="LP-01", alarm_code="LP-CLAMP-014")
    incident_id = incident["incident_id"]
    assert incident["primary_alarm_event_id"] == alarm_body["id"]

    equipment = _equipment(session, "LP-01")
    diagnosis_session_id = _create_diagnosis_session(client, field_token, equipment.id)
    linked_incident = client.get(f"/api/v1/incidents/{incident_id}", headers=_auth_header(field_token))
    assert linked_incident.status_code == 200
    assert linked_incident.json()["diagnosis_session_id"] == diagnosis_session_id

    analysis = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/analyze",
        headers=_auth_header(field_token),
    )
    assert analysis.status_code == 200
    assert analysis.json()["status"] == "COMPLETED"

    checklist = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/checklist-runs",
        headers=_auth_header(field_token),
    )
    assert checklist.status_code == 201
    checklist_body = _complete_checklist(client, field_token, checklist.json())
    assert checklist_body["status"] == "COMPLETED"

    checklist_link = client.patch(
        f"/api/v1/incidents/{incident_id}/links",
        json={"checklist_run_id": checklist_body["id"]},
        headers=_auth_header(field_token),
    )
    assert checklist_link.status_code == 200
    assert checklist_link.json()["linked_checklist_run_id"] == checklist_body["id"]

    report = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/report-drafts",
        headers=_auth_header(field_token),
    )
    assert report.status_code == 201
    report_id = report.json()["id"]

    submitted = client.post(f"/api/v1/report-drafts/{report_id}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"

    report_link = client.patch(
        f"/api/v1/incidents/{incident_id}/links",
        json={"report_draft_id": report_id},
        headers=_auth_header(field_token),
    )
    assert report_link.status_code == 200
    assert report_link.json()["linked_report_draft_id"] == report_id

    approved = client.post(
        f"/api/v1/report-drafts/{report_id}/approve",
        json={"comment": "Evidence, checklist, and incident trail reviewed."},
        headers=_auth_header(senior_token),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    approval_id = approved.json()["approvals"][0]["id"]
    approval_audit = _latest_audit_event(session, "REPORT_DRAFT_APPROVED")
    assert approval_audit.resource_id == uuid.UUID(report_id)
    assert approval_audit.actor_user_id is not None
    assert approval_audit.payload["decision"] == "APPROVED"
    assert approval_audit.payload["approval_id"] == approval_id

    approval_link = client.patch(
        f"/api/v1/incidents/{incident_id}/links",
        json={"approval_id": approval_id},
        headers=_auth_header(senior_token),
    )
    assert approval_link.status_code == 200
    assert approval_link.json()["linked_approval_id"] == approval_id

    for target_status in ("TRIAGED", "CHECKLIST_IN_PROGRESS", "REPORT_SUBMITTED", "APPROVED", "CLOSED"):
        transition = client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": target_status},
            headers=_auth_header(senior_token),
        )
        assert transition.status_code == 200
        assert transition.json()["status"] == target_status

    final_incident = client.get(f"/api/v1/incidents/{incident_id}", headers=_auth_header(senior_token))
    assert final_incident.status_code == 200
    assert final_incident.json()["status"] == "CLOSED"
    assert final_incident.json()["closed_at"] is not None
    incident_status_audits = session.scalars(
        select(AuditEvent)
        .where(
            AuditEvent.event_type == "INCIDENT_STATUS_CHANGED",
            AuditEvent.resource_id == uuid.UUID(incident_id),
        )
        .order_by(AuditEvent.created_at.asc())
    ).all()
    assert {event.payload["to_status"] for event in incident_status_audits} >= {
        "TRIAGED",
        "CHECKLIST_IN_PROGRESS",
        "REPORT_SUBMITTED",
        "APPROVED",
        "CLOSED",
    }
    closed_audit = _latest_audit_event(session, "INCIDENT_CLOSED")
    assert closed_audit.resource_id == uuid.UUID(incident_id)
    assert closed_audit.payload["to_status"] == "CLOSED"

    audit_types = _audit_types(session)
    assert {
        "EQUIPMENT_ALARM_EVENT_INGESTED",
        "INCIDENT_LINKED_TO_ALARM_EVENT",
        "DIAGNOSIS_SESSION_CREATED",
        "INCIDENT_LINKED_TO_DIAGNOSIS",
        "AGENT_ANALYSIS_COMPLETED",
        "CHECKLIST_RUN_CREATED",
        "CHECKLIST_ITEM_COMPLETED",
        "REPORT_DRAFT_CREATED",
        "REPORT_DRAFT_SUBMITTED",
        "REPORT_DRAFT_APPROVED",
        "INCIDENT_LINKED_TO_CHECKLIST",
        "INCIDENT_LINKED_TO_REPORT",
        "INCIDENT_LINKED_TO_APPROVAL",
        "INCIDENT_STATUS_CHANGED",
        "INCIDENT_CLOSED",
    }.issubset(audit_types)


def test_field_user_cannot_approve_end_to_end_report(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    report = _create_submitted_report(client, session, field_token)

    unauthenticated = client.post(f"/api/v1/report-drafts/{report['id']}/approve")
    approve = client.post(f"/api/v1/report-drafts/{report['id']}/approve", headers=_auth_header(field_token))
    reject = client.post(
        f"/api/v1/report-drafts/{report['id']}/reject",
        json={"comment": "Senior/admin approval is required for final decision."},
        headers=_auth_header(field_token),
    )

    assert unauthenticated.status_code == 401
    assert approve.status_code == 403
    assert reject.status_code == 403
    persisted = session.scalar(select(ReportDraft).where(ReportDraft.id == uuid.UUID(report["id"])))
    assert persisted is not None
    assert persisted.status == "SUBMITTED"

    denials = session.scalars(
        select(AuditEvent)
        .where(AuditEvent.event_type == "RBAC_PERMISSION_DENIED")
        .order_by(AuditEvent.created_at.asc())
    ).all()
    assert len(denials) == 2
    for denial in denials:
        assert denial.actor_user_id is not None
        assert denial.payload["role"] == "FIELD_ENGINEER"
        assert denial.payload["path_params"]["report_draft_id"] == report["id"]


def test_no_equipment_control_paths_in_operational_flow():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    unsafe_fragments = ("command", "control", "force", "override", "bypass", "servo", "reset", "motion", "write-output")
    for path in _api_paths(text):
        lowered = path.lower()
        for fragment in unsafe_fragments:
            assert fragment not in lowered

    assert _path_methods(text, "/api/v1/system/safety-settings") == {"get"}
    for path in (
        "/api/v1/equipment-data/alarm-events",
        "/api/v1/equipment-data/io-snapshots",
        "/api/v1/equipment-data/ethercat-status-snapshots",
    ):
        assert _path_methods(text, path) == {"get", "post"}


def test_operational_flow_audit_traceability(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")

    alarm = client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-02", source_event_id="ALM-PR29-AUDIT"),
        headers=_auth_header(senior_token),
    )
    assert alarm.status_code == 201
    alarm_event_id = alarm.json()["id"]

    incident = _incident_for(client, field_token, equipment_code="LP-02", alarm_code="LP-CLAMP-014")
    incident_id = incident["incident_id"]
    equipment = _equipment(session, "LP-02")
    diagnosis_session_id = _create_diagnosis_session(client, field_token, equipment.id)

    alarm_audit = _audit_event(session, "EQUIPMENT_ALARM_EVENT_INGESTED")
    assert alarm_audit.resource_id == uuid.UUID(alarm_event_id)
    assert alarm_audit.actor_user_id is not None
    assert alarm_audit.payload["equipment_code"] == "LP-02"

    incident_link_audit = _audit_event(session, "INCIDENT_LINKED_TO_ALARM_EVENT")
    assert incident_link_audit.resource_id == uuid.UUID(incident_id)
    assert incident_link_audit.payload["alarm_event_id"] == alarm_event_id

    diagnosis_link_audit = _latest_audit_event(session, "INCIDENT_LINKED_TO_DIAGNOSIS")
    assert diagnosis_link_audit.resource_id == uuid.UUID(incident_id)
    assert diagnosis_link_audit.payload["diagnosis_session_id"] == diagnosis_session_id


def _create_submitted_report(client: TestClient, session: Session, field_token: str) -> dict[str, object]:
    equipment = _equipment(session, "LP-01")
    diagnosis_session_id = _create_diagnosis_session(client, field_token, equipment.id)

    analysis = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/analyze",
        headers=_auth_header(field_token),
    )
    assert analysis.status_code == 200

    checklist = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/checklist-runs",
        headers=_auth_header(field_token),
    )
    assert checklist.status_code == 201
    _complete_checklist(client, field_token, checklist.json())

    report = client.post(
        f"/api/v1/diagnosis-sessions/{diagnosis_session_id}/report-drafts",
        headers=_auth_header(field_token),
    )
    assert report.status_code == 201

    submitted = client.post(f"/api/v1/report-drafts/{report.json()['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"
    return submitted.json()


def _complete_checklist(client: TestClient, token: str, checklist: dict[str, object]) -> dict[str, object]:
    current = checklist
    checklist_id = str(checklist["id"])
    for item in checklist["items"]:
        response = client.patch(
            f"/api/v1/checklist-runs/{checklist_id}/items/{item['id']}",
            json={"status": "DONE", "field_note": "Read-only inspection evidence captured."},
            headers=_auth_header(token),
        )
        assert response.status_code == 200
        current = response.json()
    return current


def _create_diagnosis_session(client: TestClient, token: str, equipment_id: uuid.UUID) -> str:
    response = client.post(
        "/api/v1/diagnosis-sessions",
        json={
            "equipment_id": str(equipment_id),
            "alarm_code": "LP-CLAMP-014",
            "symptom_summary": "Clamp command is observed but clamp done feedback is missing",
            "log_excerpt": "Read-only operational diagnostic log excerpt.",
            "ethercat_state": "OP",
            "io_snapshot": {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Read-only inspection note.",
            "risk_level": "LOW",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _alarm_event_payload(equipment_code: str, *, source_event_id: str) -> dict[str, object]:
    return {
        "equipment_code": equipment_code,
        "source_event_id": source_event_id,
        "alarm_code": "LP-CLAMP-014",
        "alarm_name": "Clamp done feedback missing",
        "severity": "HIGH",
        "event_status": "ACTIVE",
        "occurred_at": "2026-05-18T09:00:00Z",
        "source_system": "fabmind-readonly-adapter",
        "raw_payload": {"source": "alarm_stream", "alarm_code": "LP-CLAMP-014"},
    }


def _incident_for(client: TestClient, token: str, *, equipment_code: str, alarm_code: str) -> dict[str, object]:
    response = client.get(
        "/api/v1/incidents",
        params={"equipment_code": equipment_code, "alarm_code": alarm_code, "limit": 1},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    return body["items"][0]


def _audit_types(session: Session) -> set[str]:
    return set(session.scalars(select(AuditEvent.event_type)).all())


def _audit_event(session: Session, event_type: str) -> AuditEvent:
    event = session.scalar(select(AuditEvent).where(AuditEvent.event_type == event_type))
    assert event is not None
    return event


def _latest_audit_event(session: Session, event_type: str) -> AuditEvent:
    event = session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == event_type).order_by(AuditEvent.created_at.desc())
    )
    assert event is not None
    return event


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


def _api_paths(text: str) -> set[str]:
    return {line.strip().rstrip(":") for line in text.splitlines() if line.startswith("  /api/v1/")}


def _path_methods(text: str, target_path: str) -> set[str]:
    methods: set[str] = set()
    in_target = False

    for line in text.splitlines():
        if line.startswith("  /api/v1/"):
            if in_target:
                break
            in_target = line.strip().rstrip(":") == target_path
            continue

        if in_target and line.startswith("    "):
            maybe_method = line.strip().rstrip(":")
            if maybe_method in {"get", "post", "put", "patch", "delete"}:
                methods.add(maybe_method)

    return methods
