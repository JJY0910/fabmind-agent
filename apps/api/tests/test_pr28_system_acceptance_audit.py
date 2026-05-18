from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
OPENAPI = REPO_ROOT / "contracts" / "openapi.yaml"
SCHEMA = REPO_ROOT / "db" / "schema.sql"
DOCS = REPO_ROOT / "docs"
WEB_APP = REPO_ROOT / "apps" / "web" / "src" / "app"


def test_openapi_contains_release_candidate_operational_endpoints():
    text = OPENAPI.read_text(encoding="utf-8")

    required_paths = {
        "/api/v1/equipment",
        "/api/v1/incidents",
        "/api/v1/checklist-runs",
        "/api/v1/report-drafts",
        "/api/v1/approvals",
        "/api/v1/system/safety-settings",
        "/api/v1/equipment-data/alarm-events",
        "/api/v1/equipment-data/io-snapshots",
        "/api/v1/equipment-data/ethercat-status-snapshots",
        "/api/v1/health/ready",
    }

    assert required_paths.issubset(_api_paths(text))


def test_openapi_excludes_equipment_control_surfaces():
    text = OPENAPI.read_text(encoding="utf-8")
    unsafe_path_fragments = (
        "command",
        "control",
        "force",
        "override",
        "bypass",
        "servo",
        "reset",
        "motion",
    )

    for path in _api_paths(text):
        lowered = path.lower()
        for fragment in unsafe_path_fragments:
            assert fragment not in lowered

    assert _path_methods(text, "/api/v1/system/safety-settings") == {"get"}
    for path in (
        "/api/v1/equipment-data/alarm-events",
        "/api/v1/equipment-data/io-snapshots",
        "/api/v1/equipment-data/ethercat-status-snapshots",
    ):
        assert _path_methods(text, path) == {"get", "post"}


def test_schema_contains_release_candidate_operational_tables():
    text = SCHEMA.read_text(encoding="utf-8")
    required_tables = {
        "equipment_alarm_events",
        "equipment_io_snapshots",
        "equipment_ethercat_status_snapshots",
        "equipment_incidents",
        "report_drafts",
        "report_approvals",
        "audit_events",
    }

    for table in required_tables:
        assert re.search(rf"^CREATE TABLE {table}\b", text, flags=re.MULTILINE), table


def test_release_candidate_acceptance_document_exists_and_docs_avoid_forbidden_language():
    acceptance_doc = DOCS / "21_release_candidate_acceptance_audit.md"
    assert acceptance_doc.exists()

    forbidden = re.compile(
        r"demo|portfolio|professor|interviewer|presentation|toy|fake|mock-only|simulator",
        flags=re.IGNORECASE,
    )

    checked_files = [REPO_ROOT / "README.md", *DOCS.glob("*.md")]
    for path in checked_files:
        text = path.read_text(encoding="utf-8")
        assert forbidden.search(text) is None, path.relative_to(REPO_ROOT)


def test_release_candidate_frontend_routes_exist():
    required_route_files = {
        "/": WEB_APP / "page.tsx",
        "/equipment": WEB_APP / "equipment" / "page.tsx",
        "/active-incidents": WEB_APP / "active-incidents" / "page.tsx",
        "/checklists": WEB_APP / "checklists" / "page.tsx",
        "/approvals": WEB_APP / "approvals" / "page.tsx",
        "/audit-events": WEB_APP / "audit-events" / "page.tsx",
        "/settings": WEB_APP / "settings" / "page.tsx",
        "/diagnosis-sessions/[sessionId]": WEB_APP / "diagnosis-sessions" / "[sessionId]" / "page.tsx",
        "/checklist-runs/[checklistRunId]": WEB_APP / "checklist-runs" / "[checklistRunId]" / "page.tsx",
        "/report-drafts/[reportDraftId]": WEB_APP / "report-drafts" / "[reportDraftId]" / "page.tsx",
    }

    for route, path in required_route_files.items():
        assert path.exists(), route


def _api_paths(text: str) -> set[str]:
    return {line.strip().rstrip(":") for line in text.splitlines() if line.startswith("  /api/v1/")}


def _path_methods(text: str, target_path: str) -> set[str]:
    methods: set[str] = set()
    in_target = False

    for line in text.splitlines():
        if line.startswith("  /api/v1/"):
            if in_target:
                break
            in_target = line.strip().rstrip(":") == target_path
            continue

        if in_target and line.startswith("    "):
            maybe_method = line.strip().rstrip(":")
            if maybe_method in {"get", "post", "put", "patch", "delete"}:
                methods.add(maybe_method)

    return methods
