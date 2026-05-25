from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
APPROVALS_PAGE = WEB_SRC / "app" / "approvals" / "page.tsx"
APPROVAL_DRAWER = WEB_SRC / "components" / "ui" / "approval-detail-drawer.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
CHECKLIST_DRAWER = WEB_SRC / "components" / "ui" / "checklist-run-detail-drawer.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_approval_detail_drawer_exists_and_is_referenced() -> None:
    drawer = read(APPROVAL_DRAWER)
    page = read(APPROVALS_PAGE)

    assert "export function ApprovalDetailDrawer" in drawer
    assert 'role="dialog"' in drawer
    assert 'aria-modal="true"' in drawer
    assert 'aria-label="Read-only approval detail"' in drawer
    assert "Close approval detail" in drawer
    assert "ApprovalDetailDrawer" in page
    assert "selectedApproval" in page
    assert "Inspect" in page


def test_approval_drawer_uses_existing_read_only_queue_payload() -> None:
    drawer = read(APPROVAL_DRAWER)
    page = read(APPROVALS_PAGE)

    for section in (
        "Approval Overview",
        "Request Context",
        "Report / Workflow Context",
        "Risk / Review Signals",
        "Timing / Source",
        "Read-only Review Boundary",
    ):
        assert section in drawer

    assert "fetchApprovalQueue" in page
    assert "fetchApprovalDetail" not in page
    assert "DataSourceBanner" in page
    assert "OperationalTable" in page
    assert "TableStateRow" in page
    assert "StatusBadge" in page
    assert "CodePill" in page
    assert "currentUser.display_name" not in page


def test_approval_drawer_does_not_add_decision_mutation_or_secret_patterns() -> None:
    combined = f"{read(APPROVAL_DRAWER)}\n{read(APPROVALS_PAGE)}"

    for mutation_pattern in (
        "method: 'POST'",
        'method: "POST"',
        "method: 'PATCH'",
        'method: "PATCH"',
        "method: 'PUT'",
        'method: "PUT"',
        "approveReportDraft",
        "rejectReportDraft",
        "/approve",
        "/reject",
        "submitReportDraft",
        "localStorage.setItem",
    ):
        assert mutation_pattern not in combined

    assert "NEXT_PUBLIC_AUTH_TOKEN" not in combined
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in combined
    assert "NEXT_PUBLIC_JWT" not in combined
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", combined) is None


def test_approval_drawer_avoids_unsafe_action_language() -> None:
    combined = f"{read(APPROVAL_DRAWER)}\n{read(APPROVALS_PAGE)}"
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


def test_existing_fallback_auth_and_prior_drawer_guards_remain_visible() -> None:
    page = read(APPROVALS_PAGE)
    topbar = read(TOPBAR)
    api_client = read(API_CLIENT)
    incident_drawer = read(INCIDENT_DRAWER)
    checklist_drawer = read(CHECKLIST_DRAWER)

    assert "Showing deterministic reference data." in page
    assert "Backend unavailable" in page
    assert "currentUser.display_name" not in topbar
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
    assert "export function IncidentDetailDrawer" in incident_drawer
    assert "export function ChecklistRunDetailDrawer" in checklist_drawer
