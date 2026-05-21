from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE = REPO_ROOT / "docker-compose.yml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
README = REPO_ROOT / "README.md"
DEPLOYMENT_DOC = REPO_ROOT / "docs" / "25_deployment_containerization.md"
API_DOCKERFILE = REPO_ROOT / "apps" / "api" / "Dockerfile"
WEB_DOCKERFILE = REPO_ROOT / "apps" / "web" / "Dockerfile"


def test_deployment_packaging_files_exist():
    assert COMPOSE.exists()
    assert API_DOCKERFILE.exists()
    assert WEB_DOCKERFILE.exists()
    assert ENV_EXAMPLE.exists()
    assert DEPLOYMENT_DOC.exists()


def test_compose_defines_expected_local_services():
    text = COMPOSE.read_text(encoding="utf-8")
    service_names = _compose_service_names(text)

    assert {"postgres", "api", "web"}.issubset(service_names)
    assert "postgresql+psycopg://" in _service_block(text, "api")
    assert "@postgres:5432" in _service_block(text, "api")
    assert "NEXT_PUBLIC_API_BASE_URL" in _service_block(text, "web")
    assert "/api/v1/health/ready" in _service_block(text, "api")
    assert "EQUIPMENT_CONTROL_ENABLED" not in text


def test_compose_excludes_external_or_control_services():
    text = COMPOSE.read_text(encoding="utf-8").lower()
    service_names = _compose_service_names(text)
    forbidden_services = {
        "openai",
        "llm",
        "ai",
        "equipment-control",
        "equipment_control",
        "connector",
        "mail",
        "email",
        "smtp",
        "pdf",
        "redis",
        "minio",
    }

    assert service_names.isdisjoint(forbidden_services)
    for forbidden_image in ("openai", "mailhog", "smtp", "minio", "redis", "gotenberg"):
        assert f"image: {forbidden_image}" not in text


def test_compose_and_dockerfiles_have_consistent_build_contexts():
    compose_text = COMPOSE.read_text(encoding="utf-8")
    api_dockerfile = API_DOCKERFILE.read_text(encoding="utf-8")
    web_dockerfile = WEB_DOCKERFILE.read_text(encoding="utf-8")

    assert "context: ." in _service_block(compose_text, "api")
    assert "dockerfile: apps/api/Dockerfile" in _service_block(compose_text, "api")
    assert "COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/alembic.ini" in api_dockerfile
    assert "COPY apps/api/app" in api_dockerfile
    assert "COPY db/migrations" in api_dockerfile
    assert "uv run alembic upgrade head" in _service_block(compose_text, "api")

    assert "context: ./apps/web" in _service_block(compose_text, "web")
    assert "COPY package.json package-lock.json" in web_dockerfile
    assert "RUN npm ci" in web_dockerfile
    assert "RUN npm run build" in web_dockerfile
    assert 'CMD ["npm", "run", "start"' in web_dockerfile


def test_env_example_contains_non_secret_local_placeholders():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")

    for key in (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "DATABASE_URL",
        "API_PORT",
        "WEB_PORT",
        "NEXT_PUBLIC_API_BASE_URL",
        "JWT_SECRET",
        "APP_ENV",
    ):
        assert re.search(rf"^{key}=", text, flags=re.MULTILINE), key

    assert "replace-with-local" in text
    assert "EQUIPMENT_CONTROL_ENABLED" not in text
    for secret_marker in ("fabmind123", "sk-", "ghp_", "xoxb-", "BEGIN PRIVATE KEY"):
        assert secret_marker not in text


def test_readme_links_to_deployment_document():
    text = README.read_text(encoding="utf-8")

    assert "docs/25_deployment_containerization.md" in text


def test_deployment_doc_preserves_release_candidate_boundaries():
    text = _normalize(DEPLOYMENT_DOC.read_text(encoding="utf-8"))
    forbidden_claims = (
        "production ready",
        "production readiness achieved",
        "final production readiness",
        "ready for production deployment",
        "certified for production",
    )

    assert "local containerized execution only" in text
    assert "not a final production deployment certification" in text
    assert "no equipment control" in text
    assert "does not add external ai or llm runtime dependency" in text
    assert "known limitations" in text

    for claim in forbidden_claims:
        assert claim not in text


def _compose_service_names(text: str) -> set[str]:
    service_names: set[str] = set()
    in_services = False
    for line in text.splitlines():
        if line == "services:":
            in_services = True
            continue
        if in_services and line and not line.startswith(" "):
            break
        if in_services:
            match = re.match(r"^  ([a-zA-Z0-9_-]+):$", line)
            if match:
                service_names.add(match.group(1))
    return service_names


def _service_block(text: str, service_name: str) -> str:
    pattern = re.compile(rf"^  {re.escape(service_name)}:\n(?P<body>(?:    .*\n?)*)", re.MULTILINE)
    match = pattern.search(text)
    assert match, service_name
    return match.group("body")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())
