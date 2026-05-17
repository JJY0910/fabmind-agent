from __future__ import annotations

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
from app.models import (
    AuditEvent,
    ChecklistRun,
    DiagnosisSession,
    EquipmentAlarmEvent,
    EquipmentEthercatStatusSnapshot,
    EquipmentIOSnapshot,
    EquipmentIncident,
    ReportDraft,
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


def test_request_id_header_is_generated_and_preserved(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session

    generated = client.get("/api/v1/health")
    preserved = client.get("/api/v1/health", headers={"X-Request-ID": "REQ-PR25-001"})
    error_response = client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "REQ-PR25-404"})

    assert generated.status_code == 200
    assert generated.headers["X-Request-ID"]
    assert preserved.status_code == 200
    assert preserved.headers["X-Request-ID"] == "REQ-PR25-001"
    assert error_response.status_code == 404
    assert error_response.headers["X-Request-ID"] == "REQ-PR25-404"


def test_readiness_endpoint_reports_database_and_read_only_boundary(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"
    assert body["external_ai_enabled"] is False
    assert body["equipment_control_enabled"] is False
    assert body["read_only_diagnostics"] is True
    assert response.headers["X-Request-ID"]


def test_representative_list_endpoints_use_stable_pagination_shape(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    field_headers = _auth_header(_login(client, "field", "field-demo-password"))
    senior_headers = _auth_header(_login(client, "senior", "senior-demo-password"))
    field_endpoints = (
        "/api/v1/equipment",
        "/api/v1/alarms",
        "/api/v1/io-points",
        "/api/v1/ethercat-devices",
        "/api/v1/diagnosis-sessions",
        "/api/v1/incidents",
        "/api/v1/checklist-runs",
        "/api/v1/report-drafts",
        "/api/v1/equipment-data/alarm-events",
        "/api/v1/equipment-data/io-snapshots",
        "/api/v1/equipment-data/ethercat-status-snapshots",
    )

    for endpoint in field_endpoints:
        response = client.get(endpoint, params={"limit": 1, "offset": 0}, headers=field_headers)
        assert response.status_code == 200, endpoint
        body = response.json()
        assert set(("items", "total", "limit", "offset")).issubset(body), endpoint
        assert body["limit"] == 1
        assert body["offset"] == 0
        assert isinstance(body["items"], list)

    approvals = client.get("/api/v1/approvals", params={"limit": 1, "offset": 0}, headers=senior_headers)
    assert approvals.status_code == 200
    assert set(("items", "total", "limit", "offset")).issubset(approvals.json())


def test_invalid_pagination_parameters_are_rejected_consistently(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    field_headers = _auth_header(_login(client, "field", "field-demo-password"))
    senior_headers = _auth_header(_login(client, "senior", "senior-demo-password"))

    oversized_equipment = client.get("/api/v1/equipment", params={"limit": 101}, headers=field_headers)
    negative_alarms_offset = client.get("/api/v1/alarms", params={"offset": -1}, headers=field_headers)
    oversized_audit = client.get("/api/v1/audit-events", params={"limit": 201}, headers=senior_headers)
    negative_audit_offset = client.get("/api/v1/audit-events", params={"offset": -1}, headers=senior_headers)

    assert oversized_equipment.status_code == 422
    assert negative_alarms_offset.status_code == 422
    assert oversized_audit.status_code == 422
    assert negative_audit_offset.status_code == 422


def test_audit_event_console_supports_offset_pagination_and_filters(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    senior_headers = _auth_header(_login(client, "senior", "senior-demo-password"))

    response = client.get(
        "/api/v1/audit-events",
        params={"event_type": "AUDIT_CONSOLE_ACCESSED", "limit": 1, "offset": 0},
        headers=senior_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert body["items"][0]["event_type"] == "AUDIT_CONSOLE_ACCESSED"


def test_incident_error_paths_remain_clear_and_guarded(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    field_headers = _auth_header(_login(client, "field", "field-demo-password"))
    senior_headers = _auth_header(_login(client, "senior", "senior-demo-password"))

    incident_response = client.get("/api/v1/incidents", params={"limit": 1}, headers=field_headers)
    assert incident_response.status_code == 200
    incident_id = incident_response.json()["items"][0]["incident_id"]

    field_close = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "CLOSED"},
        headers=field_headers,
    )
    invalid_transition = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "REPORT_SUBMITTED"},
        headers=senior_headers,
    )

    assert field_close.status_code == 403
    assert "senior or admin" in field_close.json()["detail"]
    assert invalid_transition.status_code == 400
    assert "Invalid incident status transition" in invalid_transition.json()["detail"]


def test_schema_metadata_and_schema_sql_include_operational_indexes():
    schema_sql = (Path(__file__).resolve().parents[3] / "db" / "schema.sql").read_text(encoding="utf-8")
    migration = (
        Path(__file__).resolve().parents[3]
        / "db"
        / "migrations"
        / "versions"
        / "20260517_0008_pr25_performance_reliability.py"
    )
    assert migration.exists()

    expected_tables = {
        "equipment_alarm_events",
        "equipment_io_snapshots",
        "equipment_ethercat_status_snapshots",
        "equipment_incidents",
        "checklist_runs",
        "report_drafts",
        "audit_events",
    }
    assert expected_tables.issubset(Base.metadata.tables)

    expected_index_names = {
        "idx_checklist_runs_tenant_status_updated",
        "idx_report_drafts_tenant_status_updated",
        "idx_equipment_incidents_tenant_updated_opened",
        "idx_equipment_incidents_severity",
        "idx_audit_events_tenant_event_type_created",
        "idx_audit_events_tenant_severity_created",
        "idx_audit_events_tenant_resource_created",
    }
    table_indexes = set()
    for model in (
        ChecklistRun,
        ReportDraft,
        EquipmentIncident,
        AuditEvent,
        DiagnosisSession,
        EquipmentAlarmEvent,
        EquipmentIOSnapshot,
        EquipmentEthercatStatusSnapshot,
    ):
        table_indexes.update(index.name for index in model.__table__.indexes)
    assert expected_index_names.issubset(table_indexes)
    for index_name in expected_index_names | {"idx_diagnosis_sessions_tenant_created"}:
        assert index_name in schema_sql


def test_openapi_contract_keeps_operational_surface_safe_and_aligned():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    assert _path_methods(text, "/api/v1/health/ready") == {"get"}
    assert _path_methods(text, "/api/v1/system/safety-settings") == {"get"}
    for path in (
        "/api/v1/equipment-data/alarm-events",
        "/api/v1/equipment-data/io-snapshots",
        "/api/v1/equipment-data/ethercat-status-snapshots",
    ):
        assert _path_methods(text, path) == {"get", "post"}

    assert _path_methods(text, "/api/v1/incidents") == {"get", "post"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}") == {"get"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}/status") == {"patch"}
    assert _path_methods(text, "/api/v1/incidents/{incident_id}/links") == {"patch"}

    unsafe_fragments = ("command", "control", "force", "override", "bypass", "servo", "reset", "motion")
    for path in _api_paths(text):
        lowered = path.lower()
        for fragment in unsafe_fragments:
            assert fragment not in lowered


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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
