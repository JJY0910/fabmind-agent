# Deployment / Containerization

## Purpose

This document defines the PR-31 local containerized execution path for the FabMind Agent v0.2.0 release-candidate baseline. It packages the current read-only diagnostic API, Next.js web application, and PostgreSQL database into a repeatable local service stack.

This is local containerized execution only. It is not a final production deployment certification.

## Scope

Included services:

- `postgres`: PostgreSQL with pgvector-ready image.
- `api`: FastAPI backend for tenant-scoped operational workflow APIs.
- `web`: Next.js frontend configured through `NEXT_PUBLIC_API_BASE_URL`.

Excluded services:

- Real equipment connector.
- External AI or LLM runtime service.
- Equipment-control service.
- PDF, email, notification, or messaging service.
- Domains outside Load Port / FOUP Clamp / EtherCAT I/O.

## Prerequisites

- Docker Engine and Docker Compose v2.
- WSL users should run commands from the Linux project path: `/home/abcde/projects/fabmind-agent`.
- A local `.env` may be created from `.env.example` and adjusted for ports or local-only credentials.

Do not store real credentials in `.env.example`.

## Environment Variables

Root `.env.example` documents the non-secret local defaults:

- `APP_ENV`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `DATABASE_URL`
- `JWT_SECRET`
- `API_PORT`
- `WEB_PORT`
- `NEXT_PUBLIC_API_BASE_URL`
- `ENABLE_EXTERNAL_AI`

`DATABASE_URL` should point at the internal Compose service name `postgres` for container execution.

## Build

```bash
cd ~/projects/fabmind-agent
docker compose build
```

## Startup

```bash
cd ~/projects/fabmind-agent
docker compose up
```

Expected local endpoints:

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/api/v1/health`
- API readiness: `http://localhost:8000/api/v1/health/ready`

## Migration and Seed Procedure

The `api` service command runs Alembic migrations before starting Uvicorn:

```bash
uv run alembic upgrade head
```

For an explicit migration-only check:

```bash
cd ~/projects/fabmind-agent
docker compose run --rm api uv run alembic upgrade head
```

Seed data is not run automatically by Compose. If seed execution is required for a local operational walkthrough, run it explicitly after migrations using the existing backend seed helper from the API container or the local Python environment.

## Validation

Static PR-31 deployment packaging check:

```bash
cd apps/api
.venv/bin/pytest tests/test_pr31_deployment_containerization.py
```

Full backend validation:

```bash
cd apps/api
.venv/bin/pytest
```

Frontend validation:

```bash
cd apps/web
npm run typecheck
npm run build
```

Repository validation:

```bash
cd ~/projects/fabmind-agent
git diff --check
docker compose config
```

`docker compose config` validates static Compose syntax. It does not prove that containers start successfully.

In the current WSL validation environment used for this PR, the `docker` command was unavailable. `docker compose config`, image builds, and startup smoke checks require Docker Desktop WSL integration or an equivalent Docker Engine setup.

## Cleanup

```bash
cd ~/projects/fabmind-agent
docker compose down
docker compose down -v
rm -rf apps/web/.next apps/api/.pytest_cache
find apps/api -type d -name "__pycache__" -prune -exec rm -rf {} +
```

Use `docker compose down -v` only when the local PostgreSQL volume can be removed.

## Safety Boundaries

- Equipment integration remains read-only and inbound.
- No equipment control is included.
- The stack does not add external AI or LLM runtime dependency.
- Deterministic analysis remains the source of core diagnosis behavior.
- Human approval remains required for final report decisions.
- Audit logging remains part of sensitive workflow activity.
- The stack does not add PDF export, email sending, or notification services.

## Known Limitations

- This is local containerized execution only, not final production deployment certification.
- No real equipment connector is included yet.
- Browser full operational flow acceptance remains future work.
- Migration replay CI remains future work.
- `docker compose config` and startup checks require Docker availability in the target developer environment.
- Container runtime smoke is not claimed unless `docker compose up` is actually executed and health endpoints are checked.
- Observability remains limited to readiness, request IDs, app logs, and audit records.
