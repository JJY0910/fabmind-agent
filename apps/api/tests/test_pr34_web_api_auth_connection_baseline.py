from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
API_HELPER = REPO_ROOT / "apps" / "web" / "src" / "lib" / "api.ts"
AUTH_DEPS = REPO_ROOT / "apps" / "api" / "app" / "api" / "v1" / "deps.py"
AUTH_API = REPO_ROOT / "apps" / "api" / "app" / "api" / "v1" / "auth.py"
SECURITY = REPO_ROOT / "apps" / "api" / "app" / "core" / "security.py"
README = REPO_ROOT / "README.md"
AUTH_BASELINE_DOC = REPO_ROOT / "docs" / "26_web_api_auth_connection_baseline.md"


def test_web_api_auth_baseline_files_exist_and_are_linked():
    assert API_HELPER.exists()
    assert AUTH_DEPS.exists()
    assert AUTH_API.exists()
    assert SECURITY.exists()
    assert AUTH_BASELINE_DOC.exists()
    assert "docs/26_web_api_auth_connection_baseline.md" in README.read_text(encoding="utf-8")


def test_frontend_api_client_keeps_existing_token_boundary():
    text = API_HELPER.read_text(encoding="utf-8")

    assert "fabmind_access_token" in text
    assert "localStorage.getItem('fabmind_access_token')" in text
    assert "Bearer ${token}" in text
    assert "NEXT_PUBLIC_AUTH_TOKEN" not in text
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in text
    assert "NEXT_PUBLIC_JWT" not in text

    hardcoded_bearer = re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", text)
    assert hardcoded_bearer is None


def test_frontend_api_client_distinguishes_auth_network_and_parse_failures():
    text = API_HELPER.read_text(encoding="utf-8")

    assert "ApiClientError" in text
    assert '"unauthorized"' in text
    assert '"forbidden"' in text
    assert '"network"' in text
    assert '"invalid-json"' in text
    assert "status === 401" in text
    assert "status === 403" in text
    assert "Network failure" in text
    assert "returned invalid JSON" in text
    assert "failed with HTTP ${res.status}" in text


def test_backend_auth_mechanism_remains_bearer_and_role_enforced():
    deps_text = AUTH_DEPS.read_text(encoding="utf-8")
    auth_text = AUTH_API.read_text(encoding="utf-8")
    security_text = SECURITY.read_text(encoding="utf-8")

    assert "HTTPBearer(auto_error=False)" in deps_text
    assert "Missing bearer token" in deps_text
    assert "Invalid bearer token" in deps_text
    assert "require_roles" in deps_text
    assert "RBAC_PERMISSION_DENIED" in deps_text

    assert '@router.post("/login"' in auth_text
    assert '@router.get("/me"' in auth_text
    assert "create_access_token" in auth_text
    assert "verify_password" in auth_text

    assert 'os.getenv("JWT_SECRET"' in security_text
    assert "jwt.encode" in security_text
    assert "jwt.decode" in security_text


def test_auth_baseline_doc_records_gap_without_unsafe_shortcuts():
    text = AUTH_BASELINE_DOC.read_text(encoding="utf-8")
    normalized = _normalize(text)

    for phrase in (
        "HTTP 401",
        "Missing bearer token",
        "localStorage",
        "fabmind_access_token",
        "POST /api/v1/auth/login",
        "GET /api/v1/auth/me",
        "fallback warning banners",
        "No hardcoded bearer token",
        "No equipment control",
        "No external AI/LLM runtime dependency",
    ):
        assert phrase in text

    forbidden_claims = (
        "production ready",
        "final production readiness",
        "certified for production",
    )
    for claim in forbidden_claims:
        assert claim not in normalized

    assert "does not relax backend authentication" in normalized
    assert "does not add product features" in normalized


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())
