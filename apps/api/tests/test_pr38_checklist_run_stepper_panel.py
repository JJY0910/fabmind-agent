from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
CHECKLISTS_PAGE = WEB_SRC / "app" / "checklists" / "page.tsx"
CHECKLIST_DRAWER = WEB_SRC / "components" / "ui" / "checklist-run-detail-drawer.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_checklist_run_detail_drawer_exists_and_is_referenced() -> None:
    drawer = read(CHECKLIST_DRAWER)
    page = read(CHECKLISTS_PAGE)

    assert "export function ChecklistRunDetailDrawer" in drawer
    assert 'role="dialog"' in drawer
    assert 'aria-modal="true"' in drawer
    assert 'aria-label="Read-only checklist run detail"' in drawer
    assert "Close checklist run detail" in drawer
    assert "ChecklistRunDetailDrawer" in page
    assert "selectedChecklistRun" in page
    assert "Inspect" in page


def test_checklist_panel_uses_existing_read_only_list_payload() -> None:
    drawer = read(CHECKLIST_DRAWER)
    page = read(CHECKLISTS_PAGE)

    for section in (
        "Checklist Run Overview",
        "Equipment / Session Context",
        "Stepper / Progress",
        "Timing / Source",
        "Read-only Operational Context",
        "Related Workflow",
    ):
        assert section in drawer

    assert "Registered" in drawer
    assert "In Progress" in drawer
    assert "Review Ready" in drawer
    assert "Completed" in drawer
    assert "fetchChecklistRunList" in page
    assert "fetchChecklistRun(" not in page
    assert "DataSourceBanner" in page
    assert "OperationalTable" in page
    assert "TableStateRow" in page
    assert "StatusBadge" in page
    assert "CodePill" in page


def test_checklist_panel_does_not_add_mutation_or_secret_patterns() -> None:
    combined = f"{read(CHECKLIST_DRAWER)}\n{read(CHECKLISTS_PAGE)}"

    for mutation_pattern in (
        "method: 'POST'",
        'method: "POST"',
        "method: 'PATCH'",
        'method: "PATCH"',
        "method: 'PUT'",
        'method: "PUT"',
        "localStorage.setItem",
        "submitChecklist",
        "updateChecklist",
        "approveChecklist",
    ):
        assert mutation_pattern not in combined

    assert "NEXT_PUBLIC_AUTH_TOKEN" not in combined
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in combined
    assert "NEXT_PUBLIC_JWT" not in combined
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", combined) is None


def test_checklist_panel_avoids_unsafe_action_language() -> None:
    combined = f"{read(CHECKLIST_DRAWER)}\n{read(CHECKLISTS_PAGE)}"
    forbidden = [
        "force" + " output",
        "write" + " output",
        "bypass" + " interlock",
        "override" + " interlock",
        "servo" + " on",
        "autonomous" + " repair",
        "equipment" + " control",
        "command" + " execution",
        "repair" + " command",
    ]

    for phrase in forbidden:
        assert phrase.lower() not in combined.lower()


def test_fallback_auth_and_prior_drawer_guards_remain_visible() -> None:
    page = read(CHECKLISTS_PAGE)
    topbar = read(TOPBAR)
    api_client = read(API_CLIENT)
    incident_drawer = read(INCIDENT_DRAWER)

    assert "Showing deterministic reference data." in page
    assert "Backend unavailable" in page
    assert "currentUser.display_name" not in topbar
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
    assert "export function IncidentDetailDrawer" in incident_drawer
    assert 'aria-label="Read-only incident detail"' in incident_drawer
