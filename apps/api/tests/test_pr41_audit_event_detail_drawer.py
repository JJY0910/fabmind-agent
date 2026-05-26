from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
AUDIT_EVENTS_PAGE = WEB_SRC / "app" / "audit-events" / "page.tsx"
AUDIT_DRAWER = WEB_SRC / "components" / "ui" / "audit-event-detail-drawer.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
CHECKLIST_DRAWER = WEB_SRC / "components" / "ui" / "checklist-run-detail-drawer.tsx"
APPROVAL_DRAWER = WEB_SRC / "components" / "ui" / "approval-detail-drawer.tsx"
REPORT_CONTEXT_CARD = WEB_SRC / "components" / "ui" / "report-draft-context-card.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_audit_event_detail_drawer_exists_and_is_referenced() -> None:
    drawer = read(AUDIT_DRAWER)
    page = read(AUDIT_EVENTS_PAGE)

    assert "export function AuditEventDetailDrawer" in drawer
    assert 'role="dialog"' in drawer
    assert 'aria-modal="true"' in drawer
    assert 'aria-label="Read-only audit event detail"' in drawer
    assert "Close audit event detail" in drawer
    assert "AuditEventDetailDrawer" in page
    assert "selectedAuditEvent" in page
    assert "Inspect" in page


def test_audit_drawer_uses_existing_read_only_list_payload() -> None:
    drawer = read(AUDIT_DRAWER)
    page = read(AUDIT_EVENTS_PAGE)

    for section in (
        "Audit Event Overview",
        "Actor / Resource Context",
        "Payload Detail",
        "Workflow Traceability",
        "Safety / Policy Context",
        "Read-only audit context",
    ):
        assert section in drawer

    assert "fetchAuditEvents" in page
    assert "fetchAuditEvent(" not in page
    assert "DataSourceBanner" in page
    assert "OperationalTable" in page
    assert "TableStateRow" in page
    assert "StatusBadge" in page
    assert "CodePill" in page


def test_audit_payload_is_framed_as_read_only_evidence() -> None:
    drawer = read(AUDIT_DRAWER)
    page = read(AUDIT_EVENTS_PAGE)

    assert "Payload is displayed as read-only audit evidence" in drawer
    assert "Values are not interactive controls" in drawer
    assert "immutable audit context" in drawer
    assert "POLICY_BLOCKED" in page
    assert "SAFETY_BOUNDARY" in page


def test_audit_drawer_does_not_add_mutation_or_secret_patterns() -> None:
    combined = f"{read(AUDIT_DRAWER)}\n{read(AUDIT_EVENTS_PAGE)}"

    for mutation_pattern in (
        "method: 'POST'",
        'method: "POST"',
        "method: 'PATCH'",
        'method: "PATCH"',
        "method: 'PUT'",
        'method: "PUT"',
        "editAudit",
        "deleteAudit",
        "replayAudit",
        "exportAudit",
        "localStorage.setItem",
    ):
        assert mutation_pattern not in combined

    assert "NEXT_PUBLIC_AUTH_TOKEN" not in combined
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in combined
    assert "NEXT_PUBLIC_JWT" not in combined
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", combined) is None


def test_audit_drawer_avoids_unsafe_action_language() -> None:
    combined = f"{read(AUDIT_DRAWER)}\n{read(AUDIT_EVENTS_PAGE)}"
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
        "edit" + " audit",
        "delete" + " audit",
        "replay" + " audit",
    ]

    for phrase in forbidden:
        assert phrase.lower() not in combined.lower()


def test_existing_fallback_auth_and_prior_ui_guards_remain_visible() -> None:
    page = read(AUDIT_EVENTS_PAGE)
    topbar = read(TOPBAR)
    api_client = read(API_CLIENT)

    assert "Showing deterministic reference data." in page
    assert "Backend unavailable" in page
    assert "currentUser.display_name" not in topbar
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
    assert "export function IncidentDetailDrawer" in read(INCIDENT_DRAWER)
    assert "export function ChecklistRunDetailDrawer" in read(CHECKLIST_DRAWER)
    assert "export function ApprovalDetailDrawer" in read(APPROVAL_DRAWER)
    assert "export function ReportDraftContextCard" in read(REPORT_CONTEXT_CARD)
