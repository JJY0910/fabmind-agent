from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
REPORT_PAGE = WEB_SRC / "app" / "report-drafts" / "[reportDraftId]" / "page.tsx"
REPORT_CONTEXT_CARD = WEB_SRC / "components" / "ui" / "report-draft-context-card.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
CHECKLIST_DRAWER = WEB_SRC / "components" / "ui" / "checklist-run-detail-drawer.tsx"
APPROVAL_DRAWER = WEB_SRC / "components" / "ui" / "approval-detail-drawer.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_report_draft_context_card_exists_and_is_used_on_report_page() -> None:
    card = read(REPORT_CONTEXT_CARD)
    page = read(REPORT_PAGE)

    assert "export function ReportDraftContextCard" in card
    assert "Read-only report draft context" in card
    assert "ReportDraftContextCard" in page
    assert "report={data}" in page
    assert "dataMode={dataMode}" in page
    assert "fetchReportDraft(draftId)" in page


def test_report_context_is_structured_and_payload_honest() -> None:
    card = read(REPORT_CONTEXT_CARD)

    for section in (
        "Linked Incident / Equipment Coverage",
        "Timing / Source",
        "Read-only Report Boundary",
        "No linked incident in current read-only payload",
        "No equipment detail in current report payload",
        "Report detail is derived from the current report draft payload",
    ):
        assert section in card

    assert "diagnosis_session_id" in card
    assert "agent_run_id" in card
    assert "checklist_run_id" in card
    assert "approvals.length" in card


def test_report_context_card_is_read_only_and_secret_safe() -> None:
    card = read(REPORT_CONTEXT_CARD)

    for forbidden_pattern in (
        "method: 'POST'",
        'method: "POST"',
        "method: 'PATCH'",
        'method: "PATCH"',
        "method: 'PUT'",
        'method: "PUT"',
        "onClick",
        "<button",
        "approveReportDraft",
        "rejectReportDraft",
        "submitReportDraft",
        "localStorage.setItem",
        "generate" + " report",
        "submit" + " report",
        "finalize" + " report",
        "save" + " report",
        "edit" + " report",
    ):
        assert forbidden_pattern not in card

    assert "NEXT_PUBLIC_AUTH_TOKEN" not in card
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in card
    assert "NEXT_PUBLIC_JWT" not in card
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", card) is None


def test_report_context_avoids_unsafe_action_language() -> None:
    combined = f"{read(REPORT_CONTEXT_CARD)}\n{read(REPORT_PAGE)}"
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
    page = read(REPORT_PAGE)
    topbar = read(TOPBAR)
    api_client = read(API_CLIENT)

    assert "Backend API unavailable. Showing deterministic reference data." in page
    assert "currentUser.display_name" not in page
    assert "currentUser.display_name" not in topbar
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
    assert "export function IncidentDetailDrawer" in read(INCIDENT_DRAWER)
    assert "export function ChecklistRunDetailDrawer" in read(CHECKLIST_DRAWER)
    assert "export function ApprovalDetailDrawer" in read(APPROVAL_DRAWER)
