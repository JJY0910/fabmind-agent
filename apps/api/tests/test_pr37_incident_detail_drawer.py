from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
ACTIVE_INCIDENTS_PAGE = WEB_SRC / "app" / "active-incidents" / "page.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_incident_detail_drawer_exists_and_is_referenced() -> None:
    drawer = read(INCIDENT_DRAWER)
    page = read(ACTIVE_INCIDENTS_PAGE)

    assert "export function IncidentDetailDrawer" in drawer
    assert 'role="dialog"' in drawer
    assert 'aria-modal="true"' in drawer
    assert 'aria-label="Read-only incident detail"' in drawer
    assert "Close incident detail" in drawer
    assert "IncidentDetailDrawer" in page
    assert "selectedIncident" in page
    assert "Inspect" in page


def test_incident_drawer_uses_existing_read_only_payload() -> None:
    drawer = read(INCIDENT_DRAWER)
    page = read(ACTIVE_INCIDENTS_PAGE)

    assert "Incident Overview" in drawer
    assert "Equipment Context" in drawer
    assert "Timing / Source" in drawer
    assert "Related Workflow" in drawer
    assert "Read-only Operational Context" in drawer
    assert "fetchIncidentDetail" not in page
    assert "fetchIncidentList" in page
    assert "DataSourceBanner" in page
    assert "OperationalTable" in page
    assert "StatusBadge" in page
    assert "SeverityBadge" in page
    assert "CodePill" in page


def test_incident_drawer_does_not_introduce_mutation_or_secret_patterns() -> None:
    drawer = read(INCIDENT_DRAWER)
    page = read(ACTIVE_INCIDENTS_PAGE)
    combined = f"{drawer}\n{page}"

    assert "method: 'POST'" not in combined
    assert 'method: "POST"' not in combined
    assert "method: 'PATCH'" not in combined
    assert 'method: "PATCH"' not in combined
    assert "localStorage.setItem" not in combined
    assert "NEXT_PUBLIC_AUTH_TOKEN" not in combined
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in combined
    assert "NEXT_PUBLIC_JWT" not in combined
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", combined) is None


def test_incident_drawer_avoids_unsafe_action_language() -> None:
    combined = f"{read(INCIDENT_DRAWER)}\n{read(ACTIVE_INCIDENTS_PAGE)}"
    forbidden = [
        "force" + " output",
        "write" + " output",
        "bypass" + " interlock",
        "override" + " interlock",
        "servo" + " on",
        "autonomous" + " repair",
        "equipment" + " control",
        "repair" + " command",
        "FORCE_OP",
    ]

    for phrase in forbidden:
        assert phrase.lower() not in combined.lower()


def test_existing_auth_and_fallback_guards_remain_visible() -> None:
    page = read(ACTIVE_INCIDENTS_PAGE)
    topbar = read(TOPBAR)
    api_client = read(API_CLIENT)

    assert "Showing deterministic reference data." in page
    assert "Backend unavailable" in page
    assert "currentUser.display_name" not in topbar
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
