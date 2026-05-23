from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_API_CLIENT = REPO_ROOT / "apps" / "web" / "src" / "lib" / "api.ts"
TOPBAR = REPO_ROOT / "apps" / "web" / "src" / "components" / "layout" / "Topbar.tsx"
AUTH_API = REPO_ROOT / "apps" / "api" / "app" / "api" / "v1" / "auth.py"
AUTH_DEPS = REPO_ROOT / "apps" / "api" / "app" / "api" / "v1" / "deps.py"


def test_browser_session_helpers_use_existing_auth_endpoints() -> None:
    text = WEB_API_CLIENT.read_text(encoding="utf-8")

    assert "export async function signIn" in text
    assert 'fetchApi("/api/v1/auth/login", "Sign in"' in text
    assert "setStoredAccessToken(login.access_token)" in text
    assert 'fetchApi("/api/v1/auth/me", "Fetch current user"' in text
    assert "export function signOut" in text
    assert "clearStoredAccessToken()" in text


def test_access_token_storage_is_browser_guarded_and_not_public_env() -> None:
    text = WEB_API_CLIENT.read_text(encoding="utf-8")

    assert 'const ACCESS_TOKEN_STORAGE_KEY = "fabmind_access_token"' in text
    for storage_call in (
        "localStorage.getItem",
        "localStorage.setItem",
        "localStorage.removeItem",
    ):
        index = text.index(storage_call)
        guard_index = text.rfind('typeof window === "undefined"', 0, index)
        assert guard_index != -1
        assert index - guard_index < 220

    for forbidden in (
        "NEXT_PUBLIC_AUTH_TOKEN",
        "NEXT_PUBLIC_BEARER_TOKEN",
        "NEXT_PUBLIC_JWT",
        "AUTH_DISABLED",
        "DISABLE_AUTH",
        "BYPASS_AUTH",
        "SKIP_AUTH",
    ):
        assert forbidden not in text

    hardcoded_bearer = re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", text)
    assert hardcoded_bearer is None


def test_topbar_exposes_small_session_ui_without_route_redirects() -> None:
    text = TOPBAR.read_text(encoding="utf-8")

    for expected in (
        "signIn",
        "signOut",
        "fetchCurrentUser",
        "getStoredAccessToken",
        "currentUser.username",
        "currentUser.role",
        "Sign in",
        "Sign out",
    ):
        assert expected in text

    assert "currentUser.display_name" not in text
    assert 'action="/api/v1/auth/login"' not in text
    assert "router.push" not in text
    assert "redirect(" not in text


def test_backend_auth_policy_was_not_weakened() -> None:
    auth_text = AUTH_API.read_text(encoding="utf-8")
    deps_text = AUTH_DEPS.read_text(encoding="utf-8")

    assert '@router.post("/login"' in auth_text
    assert '@router.get("/me"' in auth_text
    assert "create_access_token" in auth_text
    assert "verify_password" in auth_text
    assert "HTTPBearer(auto_error=False)" in deps_text
    assert "Missing bearer token" in deps_text
    assert "Invalid bearer token" in deps_text

    for forbidden in ("AUTH_DISABLED", "DISABLE_AUTH", "BYPASS_AUTH", "SKIP_AUTH"):
        assert forbidden not in auth_text
        assert forbidden not in deps_text
