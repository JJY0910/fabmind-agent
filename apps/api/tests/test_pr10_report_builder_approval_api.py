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
    ChecklistRun,
    DiagnosisSession,
    Equipment,
    EquipmentFamily,
    Line,
    ReportDraft,
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


def test_create_report_draft_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_report_ready_session(client, session, token)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts", headers=_auth_header(token))

    assert response.status_code == 201
    body = response.json()
    assert body["diagnosis_session_id"] == session_id
    assert body["status"] == "DRAFT"
    assert body["title"].startswith("Diagnosis Report")
    assert "Clamp done sensor" in body["root_cause"]
    assert "LP-CLAMP-014" in body["evidence_summary"]
    assert "Do not bypass interlocks" in body["safety_notes"]
    assert _audit_count(session, "REPORT_DRAFT_CREATED") == 1


def test_create_report_draft_fails_without_completed_agent_analysis(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts", headers=_auth_header(token))

    assert response.status_code == 400
    assert "No completed agent analysis" in response.json()["detail"]


def test_create_report_draft_fails_without_valid_checklist_run(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    analyze = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert analyze.status_code == 200
    checklist = client.post(f"/api/v1/diagnosis-sessions/{session_id}/checklist-runs", headers=_auth_header(token))
    assert checklist.status_code == 201
    assert checklist.json()["status"] == "CREATED"

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts", headers=_auth_header(token))

    assert response.status_code == 400
    assert "No completed or blocked checklist run" in response.json()["detail"]


def test_get_report_draft_detail(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    session_id = _create_report_ready_session(client, session, token)
    report = _create_report_draft(client, token, session_id)

    response = client.get(f"/api/v1/report-drafts/{report['id']}", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == report["id"]
    assert body["inspection_summary"] == report["inspection_summary"]


def test_submit_report_draft_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_report_ready_session(client, session, token)
    report = _create_report_draft(client, token, session_id)

    response = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"
    assert _audit_count(session, "REPORT_DRAFT_SUBMITTED") == 1


def test_senior_approves_submitted_report(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200

    response = client.post(
        f"/api/v1/report-drafts/{report['id']}/approve",
        json={"comment": "Approved for demo workflow."},
        headers=_auth_header(senior_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["approvals"][0]["decision"] == "APPROVED"
    assert body["approvals"][0]["comment"] == "Approved for demo workflow."
    assert _audit_count(session, "REPORT_DRAFT_APPROVED") == 1


def test_senior_rejects_submitted_report_with_comment(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    senior_token = _login(client, "senior", "senior-demo-password")
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200

    response = client.post(
        f"/api/v1/report-drafts/{report['id']}/reject",
        json={"comment": "Add clearer checklist evidence before approval."},
        headers=_auth_header(senior_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["approvals"][0]["decision"] == "REJECTED"
    assert body["approvals"][0]["comment"] == "Add clearer checklist evidence before approval."
    assert _audit_count(session, "REPORT_DRAFT_REJECTED") == 1


def test_field_user_cannot_approve(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    session_id = _create_report_ready_session(client, session, field_token)
    report = _create_report_draft(client, field_token, session_id)
    submitted = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(field_token))
    assert submitted.status_code == 200

    response = client.post(f"/api/v1/report-drafts/{report['id']}/approve", headers=_auth_header(field_token))

    assert response.status_code == 403
    assert _audit_count(session, "RBAC_PERMISSION_DENIED") == 1


def test_unauthenticated_request_rejected(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    session_id = _create_report_ready_session(client, session, token)

    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/report-drafts")

    assert response.status_code == 401


def test_tenant_isolation_blocks_foreign_report_access(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    other_report = _create_other_tenant_report(session)

    response = client.get(f"/api/v1/report-drafts/{other_report.id}", headers=_auth_header(token))

    assert response.status_code == 404
    assert _audit_count(session, "REPORT_DRAFT_ACCESS_DENIED") == 1


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
            "symptom_summary": "Clamp command is issued but clamp done feedback is missing",
            "log_excerpt": "Synthetic read-only diagnostic log.",
            "ethercat_state": "OP",
            "io_snapshot": {"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False},
            "recent_action": "Synthetic inspection note.",
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


def _create_other_tenant_report(session: Session) -> ReportDraft:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR10_OTHER_TENANT"),
        code="PR10_OTHER_TENANT",
        name="PR-10 Other Synthetic Tenant",
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
        username="pr10-other-field",
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
    other_checklist_run = ChecklistRun(
        id=deterministic_uuid("checklist_run", other_tenant.code, "foreign-run"),
        tenant_id=other_tenant.id,
        diagnosis_session_id=other_session.id,
        agent_run_id=other_agent_run.id,
        created_by_user_id=other_user.id,
        status="COMPLETED",
    )
    other_report = ReportDraft(
        id=deterministic_uuid("report_draft", other_tenant.code, "foreign-report"),
        tenant_id=other_tenant.id,
        diagnosis_session_id=other_session.id,
        agent_run_id=other_agent_run.id,
        checklist_run_id=other_checklist_run.id,
        created_by_user_id=other_user.id,
        title="Foreign report",
        summary="Foreign tenant summary",
        root_cause="Foreign tenant cause",
        evidence_summary="Foreign tenant evidence",
        inspection_summary="Foreign tenant inspection",
        recommended_action="Foreign tenant action",
        safety_notes="Foreign tenant safety notes",
        status="DRAFT",
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
    session.add(other_checklist_run)
    session.flush()
    session.add(other_report)
    session.commit()
    return other_report
