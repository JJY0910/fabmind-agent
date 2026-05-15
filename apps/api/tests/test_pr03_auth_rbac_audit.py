from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from app.models import AuditEvent, Tenant
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


def test_password_hash_and_verify():
    password_hash = hash_password("local-demo-password", salt="unit-test-salt")

    assert password_hash.startswith("pbkdf2_sha256$")
    assert verify_password("local-demo-password", password_hash)
    assert not verify_password("wrong-password", password_hash)
    assert not verify_password("local-demo-password", "not-a-valid-hash")


def test_login_success_logs_audit(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session

    response = client.post("/api/v1/auth/login", json={"username": "field", "password": "field-demo-password"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "field"
    assert body["user"]["role"] == "FIELD_ENGINEER"
    assert _audit_count(session, "AUTH_LOGIN_SUCCESS") == 1


def test_login_failure_logs_audit(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session

    response = client.post("/api/v1/auth/login", json={"username": "field", "password": "wrong-password"})

    assert response.status_code == 401
    assert _audit_count(session, "AUTH_LOGIN_FAILURE") == 1


def test_current_user_me(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "senior", "senior-demo-password")

    response = client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "senior"
    assert body["role"] == "SENIOR_ENGINEER"
    assert body["tenant_id"]


def test_role_guard_blocks_field_from_audit_events(client_and_session: tuple[TestClient, Session]):
    client, session = client_and_session
    token = _login(client, "field", "field-demo-password")

    response = client.get("/api/v1/audit-events", headers=_auth_header(token))

    assert response.status_code == 403
    assert _audit_count(session, "RBAC_PERMISSION_DENIED") == 1


def test_admin_can_read_audit_events(client_and_session: tuple[TestClient, Session]):
    client, _session = client_and_session
    token = _login(client, "admin", "admin-demo-password")

    response = client.get("/api/v1/audit-events", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 2
    assert any(item["event_type"] == "AUTH_LOGIN_SUCCESS" for item in body["items"])


def test_audit_event_creation_service(client_and_session: tuple[TestClient, Session]):
    _client, session = client_and_session
    tenant = session.scalar(select(Tenant).where(Tenant.code == "FABMIND_DEMO"))
    assert tenant is not None

    event = create_audit_event(
        session,
        tenant_id=tenant.id,
        event_type="UNIT_TEST_AUDIT_EVENT",
        resource_type="test",
        resource_id=uuid.uuid4(),
        severity="INFO",
        payload={"scope": "auth-rbac-audit"},
    )
    session.commit()

    saved = session.scalar(select(AuditEvent).where(AuditEvent.id == event.id))
    assert saved is not None
    assert saved.event_type == "UNIT_TEST_AUDIT_EVENT"
    assert saved.payload == {"scope": "auth-rbac-audit"}


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _audit_count(session: Session, event_type: str) -> int:
    return session.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.event_type == event_type))

