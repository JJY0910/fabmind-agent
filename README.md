# FabMind Agent

**FabMind Agent** is a production-oriented, evidence-based troubleshooting platform for semiconductor **Load Port / FOUP Clamp / EtherCAT I/O** field operations.

It is designed for read-only diagnostics, deterministic rule-based analysis, human approval, and auditability. The system supports equipment troubleshooting workflows where every diagnosis claim must be tied to evidence and every risky recommendation must remain inside an industrial safety boundary.

## Product Mission

FabMind Agent helps field operations teams standardize semiconductor equipment troubleshooting without introducing equipment-control risk. It connects alarm codes, DI/DO snapshots, EtherCAT state, deterministic analysis, inspection checklists, report drafting, approval decisions, incident lifecycle state, and audit history into one traceable operational workflow.

The platform is intentionally narrow:

- **Load Port / FOUP Clamp** workflows for clamp, door, presence, and interlock-related troubleshooting.
- **EtherCAT I/O** workflows for slave state, link, and signal mismatch investigation.
- **Read-only diagnostics** only. The product does not send instructions to equipment or alter machine state.

## Current Release Candidate Status

FabMind Agent is currently packaged as the **v0.2.0 RC / operational acceptance baseline**. This status records the implementation-backed release-candidate scope for read-only diagnostics, deterministic rule analysis, human approval, and auditability. It is not a final deployment certification.

Release-candidate references:

- `docs/23_release_notes_v0_2_0.md`
- `docs/24_release_candidate_validation_runbook.md`
- `docs/21_release_candidate_acceptance_audit.md`
- `docs/22_end_to_end_operational_flow_acceptance.md`
- `docs/25_deployment_containerization.md`

## Safety Boundaries

- **No equipment control**: the system does not write to PLCs, initiate motion, alter outputs, or perform state-changing maintenance actions.
- **No safety mechanism defeat guidance**: the system must not recommend actions that defeat protected operating conditions.
- **No external AI runtime dependency**: deterministic rules must produce the core analysis without external AI or LLM calls.
- **Evidence-first diagnosis**: each hypothesis, inspection step, and report conclusion must trace back to alarm, I/O, EtherCAT, or stored evidence.
- **Human approval**: final report approval remains a senior/admin workflow.
- **Auditability**: sensitive actions, denied permissions, guardrail blocks, submissions, and approvals must be logged.

## Current Operational Workflow

1. **Dashboard (`/`)**: summarizes active diagnosis work, approval workload, checklist/report status, risk signals, and audit activity.
2. **Equipment Registry (`/equipment`)**: provides read-only equipment context for Load Port / FOUP Clamp / EtherCAT I/O records.
3. **Active Incidents (`/active-incidents`)**: tracks first-class incident lifecycle state across diagnosis, checklist, report, approval, and audit context.
4. **Diagnosis Session (`/diagnosis-sessions/[sessionId]`)**: captures the situation snapshot and presents deterministic agent analysis.
5. **Checklist Runs (`/checklists`, `/checklist-runs/[checklistRunId]`)**: supports field inspection execution with item status and field notes.
6. **Approval Queue and Report Detail (`/approvals`, `/report-drafts/[reportDraftId]`)**: consolidates evidence, inspection results, and approval decisions.
7. **Audit Console (`/audit-events`)**: exposes tenant-scoped audit history for sensitive workflow events.
8. **System Safety Settings (`/settings`)**: shows read-only safety policy and RBAC boundary information.

## Architecture

- **Frontend (Next.js)**: industrial operations UI built with TypeScript, Tailwind CSS, and route-based workflow pages.
- **Backend (FastAPI)**: authenticated API for equipment registry, incidents, diagnosis sessions, deterministic analysis, checklist runs, report approvals, dashboard summary, system safety settings, read-only telemetry ingestion, and audit events.
- **Database (PostgreSQL + pgvector-ready schema)**: tenant-scoped operational tables for users, roles, equipment, alarms, I/O points, EtherCAT devices, telemetry snapshots, incidents, diagnosis sessions, agent runs, checklists, reports, approvals, policy violations, and audit events.
- **Deterministic Agent Engine**: rule engine for Load Port / FOUP Clamp / EtherCAT I/O scenarios with evidence links and safety guardrails.

## Repository Structure

- `/apps/web/`: Frontend Next.js application
- `/apps/api/`: Backend FastAPI application
- `/contracts/`: OpenAPI specification (`openapi.yaml`)
- `/db/`: Database schema and seed/migration assets
- `/docs/`: Product requirements, traceability, operational workflow, quality gate, and acceptance documentation

## Validation

Frontend:

```bash
cd apps/web
npm run typecheck
npm run build
```

Backend:

```bash
cd apps/api
.venv/bin/pytest tests/test_pr30_release_candidate_packaging.py
.venv/bin/pytest
```

Repository:

```bash
git diff --check
```

## Local Containerized Execution

PR-31 adds a local Docker Compose stack for the v0.2.0 release-candidate baseline. It is intended for repeatable local service execution, not final deployment certification.

```bash
cp .env.example .env
docker compose build
docker compose up
```

See `docs/25_deployment_containerization.md` for service layout, environment variables, migration guidance, validation commands, cleanup, and known limitations.

## Current Implemented Modules

- Authentication/RBAC foundation and current-user role visibility
- Tenant-scoped equipment registry and equipment knowledge API
- Active incident lifecycle and case-management API
- Diagnosis session API
- Deterministic agent analysis API
- Checklist runner API, list hub, and detail workflow
- Report draft, approval queue, and senior/admin approval workflow
- Dashboard summary API and dashboard page
- Audit console API and audit page
- Read-only system safety settings
- Read-only equipment telemetry ingestion for alarm events, I/O snapshots, and EtherCAT status snapshots
- Request correlation ID middleware and readiness endpoint
- Frontend API contract handling with explicit degraded data state
- Local containerized execution packaging for PostgreSQL, API, and web services

## Release Direction

PR-31 packages local deployment/containerization for the v0.2.0 release candidate baseline with Docker Compose, API/web Dockerfiles, environment examples, deployment documentation, and static deployment checks. Next release work should focus on observability and incident timeline hardening, read-only connector specification, offline factory network execution mode, browser full operational flow acceptance, and migration replay CI.

See:

- `docs/11_operational_workflow_guide.md`
- `docs/12_product_requirements_v1.md`
- `docs/13_module_traceability_matrix.md`
- `docs/14_industrial_quality_gate.md`
- `docs/15_implementation_roadmap_v2.md`
- `docs/21_release_candidate_acceptance_audit.md`
- `docs/22_end_to_end_operational_flow_acceptance.md`
- `docs/23_release_notes_v0_2_0.md`
- `docs/24_release_candidate_validation_runbook.md`
- `docs/25_deployment_containerization.md`
