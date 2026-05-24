from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
OPERATIONAL_UI = WEB_SRC / "components" / "ui" / "operational.tsx"
EQUIPMENT_PAGE = WEB_SRC / "app" / "equipment" / "page.tsx"
INCIDENTS_PAGE = WEB_SRC / "app" / "active-incidents" / "page.tsx"
AUDIT_PAGE = WEB_SRC / "app" / "audit-events" / "page.tsx"
TOPBAR = WEB_SRC / "components" / "layout" / "Topbar.tsx"
API_CLIENT = WEB_SRC / "lib" / "api.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_shared_operational_ui_components_exist() -> None:
    source = read(OPERATIONAL_UI)

    for export_name in (
        "export function StatusBadge",
        "export function SeverityBadge",
        "export function CodePill",
        "export function DataSourceBanner",
        "export function OperationalTable",
        "export function TableStateRow",
    ):
        assert export_name in source


def test_target_routes_use_shared_state_density_components() -> None:
    for page in (EQUIPMENT_PAGE, INCIDENTS_PAGE, AUDIT_PAGE):
        source = read(page)
        assert "@/components/ui/operational" in source
        assert "DataSourceBanner" in source
        assert "OperationalTable" in source
        assert "TableStateRow" in source

    assert "StatusBadge" in read(EQUIPMENT_PAGE)
    assert "SeverityBadge" in read(INCIDENTS_PAGE)
    assert "StatusBadge" in read(AUDIT_PAGE)


def test_fallback_banners_and_auth_safety_are_preserved() -> None:
    for page in (EQUIPMENT_PAGE, INCIDENTS_PAGE, AUDIT_PAGE):
        source = read(page)
        assert "Backend unavailable" in source
        assert "Showing deterministic reference data." in source

    topbar = read(TOPBAR)
    assert "currentUser.display_name" not in topbar

    api_client = read(API_CLIENT)
    assert "Bearer ${token}" in api_client
    assert "fabmind_access_token" in api_client
    assert "NEXT_PUBLIC_AUTH_TOKEN" not in api_client
    assert "NEXT_PUBLIC_BEARER_TOKEN" not in api_client
    assert "NEXT_PUBLIC_JWT" not in api_client
    assert re.search(r"Bearer\s+(?!\$\{token\})[A-Za-z0-9._-]{12,}", api_client) is None


def test_target_routes_avoid_forbidden_product_language() -> None:
    forbidden = re.compile(
        r"demo|portfolio|professor|interviewer|presentation|toy|fake|mock-only|simulator",
        re.IGNORECASE,
    )

    for path in (OPERATIONAL_UI, EQUIPMENT_PAGE, INCIDENTS_PAGE, AUDIT_PAGE):
        assert forbidden.search(read(path)) is None
