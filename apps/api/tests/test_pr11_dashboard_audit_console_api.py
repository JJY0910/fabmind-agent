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
from app.services.audit import create_audit_event


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


def test_dashboard_summary_success(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    _create_analyzed_session(client, session, token)

    response = client.get("/api/v1/dashboard/summary", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["active_diagnosis_count"] == 1
    assert body["pending_approval_count"] == 0
    assert body["high_risk_count"] == 0
    assert body["evidence_linked_rate"] > 0
    assert body["open_checklist_count"] == 0
    assert body["guardrail_blocks_today"] == 0


def test_dashboard_summary_is_tenant_scoped(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    _create_other_tenant_diagnosis_session(session)
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/dashboard/summary", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["active_diagnosis_count"] == 0
    assert body["high_risk_count"] == 0
    assert body["recent_diagnosis_sessions"] == []


def test_dashboard_recent_diagnosis_sessions_included(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    equipment = _equipment(session, "LP-02")
    session_id = _create_diagnosis_session(client, token, equipment.id)

    response = client.get("/api/v1/dashboard/summary", headers=_auth_header(token))

    assert response.status_code == 200
    recent = response.json()["recent_diagnosis_sessions"]
    assert recent[0]["session_id"] == session_id
    assert recent[0]["equipment_code"] == "LP-02"
    assert recent[0]["alarm_code"] == "LP-CLAMP-014"


def test_dashboard_required_actions_included(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")
    equipment = _equipment(session, "LP-01")
    _create_diagnosis_session(client, token, equipment.id, risk_level="HIGH")
    _create_blocked_checklist(client, session, token)
    _create_submitted_report(client, session, token)

    response = client.get("/api/v1/dashboard/summary", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    action_types = {item["action_type"] for item in body["required_actions"]}
    assert "HIGH_RISK_DIAGNOSIS" in action_types
    assert "BLOCKED_CHECKLIST_ITEM" in action_types
    assert "REPORT_APPROVAL" in action_types
    assert body["pending_approval_count"] == 1
    assert body["open_checklist_count"] == 1
    assert body["submitted_report_count"] == 1


@pytest.mark.parametrize(
    ("username", "password"),
    [("senior", "senior-demo-password"), ("admin", "admin-demo-password")],
)
def test_audit_console_senior_admin_success(
    client_and_session: tuple[TestClient, Session],
    username: str,
    password: str,
):
    client, _session = client_and_session
    token = _login(client, username, password)

    response = client.get("/api/v1/audit-events", headers=_auth_header(token))

    assert response.status_code == 200
    assert any(item["event_type"] == "AUDIT_CONSOLE_ACCESSED" for item in response.json()["items"])


def test_audit_console_field_denied_logs_permission_audit(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/audit-events", headers=_auth_header(token))

    assert response.status_code == 403
    assert _audit_count(session, "RBAC_PERMISSION_DENIED") == 1


def test_audit_event_filters_work(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    tenant = _tenant(session)
    create_audit_event(
        session,
        tenant_id=tenant.id,
        event_type="PR11_FILTER_TARGET",
        resource_type="report_draft",
        resource_id=uuid.uuid4(),
        severity="WARNING",
        payload={"scope": "dashboard-audit-console"},
    )
    create_audit_event(
        session,
        tenant_id=tenant.id,
        event_type="PR11_FILTER_OTHER",
        resource_type="diagnosis_session",
        resource_id=uuid.uuid4(),
        severity="INFO",
        payload={"scope": "dashboard-audit-console"},
    )
    session.commit()
    token = _login(client, "senior", "senior-demo-password")

    response = client.get(
        "/api/v1/audit-events",
        params={
            "event_type": "PR11_FILTER_TARGET",
            "severity": "WARNING",
            "resource_type": "report_draft",
            "limit": 1,
        },
        headers=_auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["event_type"] == "PR11_FILTER_TARGET"
    assert body["items"][0]["resource_type"] == "report_draft"


def test_unauthenticated_request_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401


def _create_analyzed_session(client: TestClient, session: Session, token: str) -> str:
    equipment = _equipment(session, "LP-01")
    session_id = _create_diagnosis_session(client, token, equipment.id)
    response = client.post(f"/api/v1/diagnosis-sessions/{session_id}/analyze", headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    return session_id


def _create_blocked_checklist(client: TestClient, session: Session, token: str) -> dict[str, object]:
    session_id = _create_analyzed_session(client, session, token)
    checklist = _create_checklist_run(client, token, session_id)
    item_id = checklist["items"][0]["id"]
    response = client.patch(
        f"/api/v1/checklist-runs/{checklist['id']}/items/{item_id}",
        json={"status": "BLOCKED", "field_note": "Senior review required before continuing."},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "BLOCKED"
    return response.json()


def _create_submitted_report(client: TestClient, session: Session, token: str) -> dict[str, object]:
    session_id = _create_report_ready_session(client, session, token)
    report = _create_report_draft(client, token, session_id)
    response = client.post(f"/api/v1/report-drafts/{report['id']}/submit", headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"
    return response.json()


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


def _create_other_tenant_diagnosis_session(session: Session) -> DiagnosisSession:
    other_tenant = Tenant(
        id=deterministic_uuid("tenant", "PR11_OTHER_TENANT"),
        code="PR11_OTHER_TENANT",
        name="PR-11 Other Synthetic Tenant",
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
        username="pr11-other-field",
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
        risk_level="CRITICAL",
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
