from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
WEB_APP = WEB_SRC / "app"
TRACE_COMPONENT = WEB_SRC / "components" / "ui" / "workflow-trace.tsx"
INCIDENT_DRAWER = WEB_SRC / "components" / "ui" / "incident-detail-drawer.tsx"
CHECKLIST_DRAWER = WEB_SRC / "components" / "ui" / "checklist-run-detail-drawer.tsx"
APPROVAL_DRAWER = WEB_SRC / "components" / "ui" / "approval-detail-drawer.tsx"
AUDIT_DRAWER = WEB_SRC / "components" / "ui" / "audit-event-detail-drawer.tsx"
REPORT_CONTEXT_CARD = WEB_SRC / "components" / "ui" / "report-draft-context-card.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


TRACE_SURFACES = [
    INCIDENT_DRAWER,
    CHECKLIST_DRAWER,
    APPROVAL_DRAWER,
    AUDIT_DRAWER,
    REPORT_CONTEXT_CARD,
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_route_inventory_allows_only_existing_target_specific_links() -> None:
    assert (WEB_APP / "report-drafts" / "[reportDraftId]" / "page.tsx").exists()
    assert (WEB_APP / "checklist-runs" / "[checklistRunId]" / "page.tsx").exists()
    assert (WEB_APP / "diagnosis-sessions" / "[sessionId]" / "page.tsx").exists()

    assert not (WEB_APP / "active-incidents" / "[incidentId]" / "page.tsx").exists()
    assert not (WEB_APP / "approvals" / "[approvalId]" / "page.tsx").exists()
    assert not (WEB_APP / "audit-events" / "[auditEventId]" / "page.tsx").exists()
    assert not (WEB_APP / "equipment" / "[equipmentId]" / "page.tsx").exists()


def test_workflow_trace_component_centralizes_supported_route_helpers() -> None:
    trace = read(TRACE_COMPONENT)

    assert "export function WorkflowTraceList" in trace
    assert "export function reportDraftTraceHref" in trace
    assert "export function checklistRunTraceHref" in trace
    assert "export function diagnosisSessionTraceHref" in trace
    assert '"report-drafts" | "checklist-runs" | "diagnosis-sessions"' in trace

    for unsupported_route in ("/active-incidents/", "/approvals/", "/audit-events/", "/equipment/"):
        assert unsupported_route not in trace


def test_workflow_trace_is_used_on_existing_read_only_surfaces() -> None:
    for path in TRACE_SURFACES:
        text = read(path)
        assert "WorkflowTraceList" in text

    assert "reportDraftTraceHref(approval.report_draft_id)" in read(APPROVAL_DRAWER)
    assert "reportDraftTraceHref(reportDraftId)" in read(CHECKLIST_DRAWER)
    assert "reportDraftTraceHref(reportDraftId)" in read(INCIDENT_DRAWER)
    assert "diagnosisSessionTraceHref(report.diagnosis_session_id)" in read(REPORT_CONTEXT_CARD)
    assert "checklistRunTraceHref(checklistRunId)" in read(AUDIT_DRAWER)


def test_unsupported_ids_remain_non_clickable_trace_references() -> None:
    combined = "\n".join(read(path) for path in TRACE_SURFACES)

    for unsupported_dynamic_link in (
        "/active-incidents/${",
        "/approvals/${",
        "/audit-events/${",
        "/equipment/${",
        "incidentTraceHref",
        "approvalTraceHref",
        "auditEventTraceHref",
        "equipmentTraceHref",
    ):
        assert unsupported_dynamic_link not in combined

    assert "No target-specific incident route is currently available" in combined
    assert "Approval queue is list-based in the current route set" in combined
    assert "Audit console is list-based in the current route set" in combined
    assert "Equipment registry is list-based in the current route set" in combined


def test_trace_polish_does_not_add_mutation_or_secret_patterns() -> None:
    combined = f"{read(TRACE_COMPONENT)}\n" + "\n".join(read(path) for path in TRACE_SURFACES)

    for mutation_pattern in (
        "method: 'POST'",
        'method: "POST"',
        "method: 'PATCH'",
        'method: "PATCH"',
        "method: 'PUT'",
        'method: "PUT"',
        "localStorage.setItem",
        "generateReport",
        "submitReport",
        "finalizeReport",
        "saveReport",
        "editReport",
        "approveNow",
        "rejectNow",
        "deleteAudit",
        "replayAudit",
    ):
        assert mutation_pattern not in combined

    assert "NEXT_PUBLIC_AUTH_TOKEN" not in combined
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in combined
    assert "NEXT_PUBLIC_JWT" not in combined
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", combined) is None


def test_existing_boundaries_and_session_display_guards_remain() -> None:
    combined = "\n".join(read(path) for path in TRACE_SURFACES)

    assert "This panel displays immutable audit context only" in read(AUDIT_DRAWER)
    assert "This panel does not generate, submit, or mutate report records." in read(REPORT_CONTEXT_CARD)
    assert "Values are not interactive controls" in read(AUDIT_DRAWER)
    assert "currentUser.display_name" not in read(TOPBAR)
    assert "Bearer ${token}" in read(API_CLIENT)
    assert "fabmind_access_token" in read(API_CLIENT)
    assert "Read-only detail route available" in combined or "Read-only report route available" in combined
