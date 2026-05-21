from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS = REPO_ROOT / "docs"
README = REPO_ROOT / "README.md"
RELEASE_NOTES = DOCS / "23_release_notes_v0_2_0.md"
VALIDATION_RUNBOOK = DOCS / "24_release_candidate_validation_runbook.md"
ACCEPTANCE_AUDIT = DOCS / "21_release_candidate_acceptance_audit.md"
OPERATIONAL_FLOW_ACCEPTANCE = DOCS / "22_end_to_end_operational_flow_acceptance.md"


def test_release_candidate_packaging_documents_exist():
    assert RELEASE_NOTES.exists()
    assert VALIDATION_RUNBOOK.exists()
    assert ACCEPTANCE_AUDIT.exists()
    assert OPERATIONAL_FLOW_ACCEPTANCE.exists()


def test_readme_links_to_release_candidate_packaging_documents():
    text = README.read_text(encoding="utf-8")

    assert "docs/23_release_notes_v0_2_0.md" in text
    assert "docs/24_release_candidate_validation_runbook.md" in text
    assert "docs/21_release_candidate_acceptance_audit.md" in text
    assert "docs/22_end_to_end_operational_flow_acceptance.md" in text


def test_release_notes_avoid_forbidden_product_language():
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    forbidden = re.compile(
        r"demo|portfolio|professor|interviewer|presentation|toy|fake|mock-only|simulator",
        flags=re.IGNORECASE,
    )

    assert forbidden.search(text) is None


def test_release_notes_do_not_claim_final_production_readiness():
    text = _normalize(RELEASE_NOTES.read_text(encoding="utf-8"))
    forbidden_claims = (
        "production ready",
        "production readiness achieved",
        "final production readiness",
        "ready for production deployment",
        "certified for production",
    )

    assert "fabmind agent v0.2.0 release candidate" in text
    assert "release candidate / operational acceptance baseline" in text

    for claim in forbidden_claims:
        assert claim not in text


def test_release_notes_include_no_equipment_control_boundary():
    text = _normalize(RELEASE_NOTES.read_text(encoding="utf-8"))

    assert "no equipment control" in text


def test_validation_runbook_includes_required_commands():
    text = VALIDATION_RUNBOOK.read_text(encoding="utf-8")

    for command in (".venv/bin/pytest", "npm run typecheck", "npm run build", "git diff --check"):
        assert command in text

    assert "[d]emo|[p]ortfolio|[p]rofessor|[i]nterviewer" in text
    assert "[L]octite|re[-]tighten|force[[:space:]]output" in text


def test_validation_runbook_names_github_actions_as_playwright_source_of_truth():
    text = _normalize(VALIDATION_RUNBOOK.read_text(encoding="utf-8"))

    assert "github actions" in text
    assert "playwright source of truth" in text


def test_release_notes_include_known_limitations():
    text = _normalize(RELEASE_NOTES.read_text(encoding="utf-8"))

    assert "known limitations" in text
    assert "not connected to real fab equipment yet" in text


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())
