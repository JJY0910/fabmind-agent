from __future__ import annotations

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
from app.models import AuditEvent, Equipment, EquipmentIOSnapshot, Tenant


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


def test_unauthenticated_ingestion_is_rejected(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session

    response = client.post("/api/v1/equipment-data/alarm-events", json=_alarm_event_payload("LP-01", "HIGH"))

    assert response.status_code == 401


def test_field_user_ingestion_is_rejected_but_query_is_allowed(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    field_token = _login(client, "field", "field-demo-password")
    admin_token = _login(client, "admin", "admin-demo-password")

    denied_response = client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-01", "HIGH", source_event_id="ALM-FIELD-DENIED"),
        headers=_auth_header(field_token),
    )
    assert denied_response.status_code == 403

    audit = session.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == "RBAC_PERMISSION_DENIED",
            AuditEvent.resource_type == "api_route",
        )
    )
    assert audit is not None
    assert audit.payload["method"] == "POST"

    assert client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-01", "HIGH", source_event_id="ALM-READBACK"),
        headers=_auth_header(admin_token),
    ).status_code == 201

    query_response = client.get(
        "/api/v1/equipment-data/alarm-events",
        headers=_auth_header(field_token),
    )
    assert query_response.status_code == 200
    assert query_response.json()["total"] == 1


def test_authenticated_alarm_event_ingestion_succeeds_and_audits(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    response = client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-01", "HIGH", source_event_id="ALM-001"),
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["equipment_code"] == "LP-01"
    assert body["alarm_code"] == "LP-CLAMP-014"
    assert body["severity"] == "HIGH"
    assert body["event_status"] == "ACTIVE"
    assert body["source_event_id"] == "ALM-001"

    audit = session.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == "EQUIPMENT_ALARM_EVENT_INGESTED",
            AuditEvent.resource_type == "equipment_alarm_event",
        )
    )
    assert audit is not None
    assert audit.payload["equipment_code"] == "LP-01"


def test_authenticated_io_snapshot_ingestion_succeeds(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    response = client.post(
        "/api/v1/equipment-data/io-snapshots",
        json=_io_snapshot_payload("LP-01"),
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["equipment_code"] == "LP-01"
    assert body["observed_inputs"]["DI_CLAMP_DONE"] is False
    assert body["observed_outputs"]["DO_CLAMP_SOL"] is True


def test_authenticated_ethercat_status_snapshot_ingestion_succeeds(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    response = client.post(
        "/api/v1/equipment-data/ethercat-status-snapshots",
        json=_ethercat_snapshot_payload("LP-01"),
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["equipment_code"] == "LP-01"
    assert body["master_state"] == "OP"
    assert body["slave_count"] == 6
    assert body["working_counter"] == 12


def test_list_endpoints_return_persisted_records_with_pagination_and_filters(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    ingest_token = _login(client, "admin", "admin-demo-password")
    query_token = _login(client, "field", "field-demo-password")
    ingest_headers = _auth_header(ingest_token)
    query_headers = _auth_header(query_token)

    assert client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-01", "HIGH", source_event_id="ALM-001"),
        headers=ingest_headers,
    ).status_code == 201
    assert client.post(
        "/api/v1/equipment-data/alarm-events",
        json=_alarm_event_payload("LP-02", "LOW", source_event_id="ALM-002"),
        headers=ingest_headers,
    ).status_code == 201
    assert client.post(
        "/api/v1/equipment-data/io-snapshots",
        json=_io_snapshot_payload("LP-01"),
        headers=ingest_headers,
    ).status_code == 201
    assert client.post(
        "/api/v1/equipment-data/ethercat-status-snapshots",
        json=_ethercat_snapshot_payload("LP-01"),
        headers=ingest_headers,
    ).status_code == 201

    alarms_page = client.get(
        "/api/v1/equipment-data/alarm-events",
        params={"limit": 1, "offset": 0},
        headers=query_headers,
    )
    assert alarms_page.status_code == 200
    assert alarms_page.json()["total"] == 2
    assert alarms_page.json()["limit"] == 1

    high_alarm = client.get(
        "/api/v1/equipment-data/alarm-events",
        params={"equipment_code": "LP-01", "risk_level": "HIGH"},
        headers=query_headers,
    )
    assert high_alarm.status_code == 200
    assert high_alarm.json()["total"] == 1
    assert high_alarm.json()["items"][0]["equipment_code"] == "LP-01"

    io_list = client.get(
        "/api/v1/equipment-data/io-snapshots",
        params={"equipment_code": "LP-01"},
        headers=query_headers,
    )
    assert io_list.status_code == 200
    assert io_list.json()["total"] == 1
    assert io_list.json()["items"][0]["observed_inputs"]["DI_CLAMP_DONE"] is False

    ethercat_list = client.get(
        "/api/v1/equipment-data/ethercat-status-snapshots",
        params={"equipment_code": "LP-01"},
        headers=query_headers,
    )
    assert ethercat_list.status_code == 200
    assert ethercat_list.json()["total"] == 1
    assert ethercat_list.json()["items"][0]["master_state"] == "OP"


def test_pagination_rejects_out_of_bounds_parameters(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "field", "field-demo-password")
    headers = _auth_header(token)

    oversized_limit = client.get(
        "/api/v1/equipment-data/alarm-events",
        params={"limit": 101},
        headers=headers,
    )
    negative_offset = client.get(
        "/api/v1/equipment-data/alarm-events",
        params={"offset": -1},
        headers=headers,
    )

    assert oversized_limit.status_code == 422
    assert negative_offset.status_code == 422


def test_normal_telemetry_summary_is_accepted_without_command_intent(
    client_and_session: tuple[TestClient, Session],
):
    client, _session = client_and_session
    token = _login(client, "senior", "senior-demo-password")
    payload = _alarm_event_payload("LP-01", "MEDIUM", source_event_id="ALM-OBSERVATION")
    payload["raw_payload"] = {
        "alarm_summary": "Observed operator note references override history without requesting action",
        "source": "alarm_stream",
    }

    response = client.post(
        "/api/v1/equipment-data/alarm-events",
        json=payload,
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    assert response.json()["source_event_id"] == "ALM-OBSERVATION"


def test_unsafe_command_like_ingestion_payload_is_rejected_and_audited(
    client_and_session: tuple[TestClient, Session],
):
    client, session = client_and_session
    token = _login(client, "admin", "admin-demo-password")
    payload = _io_snapshot_payload("LP-01")
    payload["raw_payload"] = {"command_intent": "change actuator state"}

    response = client.post("/api/v1/equipment-data/io-snapshots", json=payload, headers=_auth_header(token))

    assert response.status_code == 400
    assert "Read-only equipment ingestion rejected" in response.json()["detail"]
    assert "change actuator state" not in response.json()["detail"]
    snapshot_count = session.scalar(select(func.count()).select_from(EquipmentIOSnapshot))
    assert snapshot_count == 0
    audit = session.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == "EQUIPMENT_DATA_INGESTION_BLOCKED",
            AuditEvent.resource_type == "equipment_io_snapshot",
        )
    )
    assert audit is not None


def test_openapi_contains_only_read_only_equipment_data_endpoints():
    contract = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    text = contract.read_text(encoding="utf-8")

    expected_paths = {
        "/api/v1/equipment-data/alarm-events": {"get", "post"},
        "/api/v1/equipment-data/io-snapshots": {"get", "post"},
        "/api/v1/equipment-data/ethercat-status-snapshots": {"get", "post"},
    }
    for path, expected_methods in expected_paths.items():
        assert _path_methods(text, path) == expected_methods

    for path in _equipment_data_paths(text):
        lowered = path.lower()
        for unsafe_fragment in ("command", "control", "force", "override", "bypass", "servo", "reset", "motion"):
            assert unsafe_fragment not in lowered


def _alarm_event_payload(equipment_code: str, severity: str, *, source_event_id: str = "ALM-001") -> dict[str, object]:
    return {
        "equipment_code": equipment_code,
        "source_event_id": source_event_id,
        "alarm_code": "LP-CLAMP-014",
        "alarm_name": "Clamp done feedback missing",
        "severity": severity,
        "event_status": "ACTIVE",
        "occurred_at": "2026-05-16T09:00:00Z",
        "source_system": "fabmind-readonly-adapter",
        "raw_payload": {"source": "alarm_stream", "alarm_code": "LP-CLAMP-014"},
    }


def _io_snapshot_payload(equipment_code: str) -> dict[str, object]:
    return {
        "equipment_code": equipment_code,
        "source_snapshot_id": "IO-001",
        "captured_at": "2026-05-16T09:01:00Z",
        "source_system": "fabmind-readonly-adapter",
        "observed_inputs": {"DI_CLAMP_DONE": False, "DI_FOUP_PRESENT": True},
        "observed_outputs": {"DO_CLAMP_SOL": True},
        "raw_payload": {"source": "io_monitor", "sample_index": 1},
    }


def _ethercat_snapshot_payload(equipment_code: str) -> dict[str, object]:
    return {
        "equipment_code": equipment_code,
        "source_snapshot_id": "ECAT-001",
        "captured_at": "2026-05-16T09:02:00Z",
        "source_system": "fabmind-readonly-adapter",
        "master_state": "OP",
        "slave_count": 6,
        "working_counter": 12,
        "link_status": "LINK_UP",
        "error_code": None,
        "error_summary": None,
        "raw_payload": {"source": "ethercat_monitor", "wkc": 12},
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


def _equipment_data_paths(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("/api/v1/equipment-data/") and stripped.endswith(":"):
            paths.append(stripped.rstrip(":"))
    return paths
