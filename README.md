# FabMind Agent

**FabMind Agent** is a production-oriented, evidence-based troubleshooting platform for semiconductor **Load Port / FOUP Clamp / EtherCAT I/O** field operations.

It is designed for read-only diagnostics, deterministic rule-based analysis, human approval, and auditability. The system supports equipment troubleshooting workflows where every diagnosis claim must be tied to evidence and every risky recommendation must remain inside an industrial safety boundary.

## Product Mission

FabMind Agent helps field operations teams standardize semiconductor equipment troubleshooting without introducing equipment-control risk. It connects alarm codes, DI/DO snapshots, EtherCAT state, deterministic analysis, inspection checklists, report drafting, approval decisions, and audit history into one traceable operational workflow.

The platform is intentionally narrow:

- **Load Port / FOUP Clamp** workflows for clamp, door, presence, and interlock-related troubleshooting.
- **EtherCAT I/O** workflows for slave state, link, and signal mismatch investigation.
- **Read-only diagnostics** only. The product does not send commands to equipment or alter machine state.

## Safety Boundaries

- **No equipment control**: no PLC writes, motion commands, servo commands, output forcing, or state-changing maintenance actions.
- **No interlock bypass**: the system must not recommend defeating safety mechanisms.
- **No external AI runtime dependency**: deterministic rules must produce the core analysis without external AI or LLM calls.
- **Evidence-first diagnosis**: each hypothesis, inspection step, and report conclusion must trace back to alarm, I/O, EtherCAT, or stored evidence.
- **Human approval**: final report approval remains a senior/admin workflow.
- **Auditability**: sensitive actions, denied permissions, guardrail blocks, submissions, and approvals must be logged.

## Current Operational Workflow

1. **Dashboard (`/`)**: summarizes active diagnosis work, approval workload, checklist/report status, risk signals, and audit activity.
2. **Diagnosis Session (`/diagnosis-sessions/[sessionId]`)**: captures the situation snapshot and presents deterministic agent analysis.
3. **Checklist Run (`/checklist-runs/[checklistRunId]`)**: supports field inspection execution with item status and field notes.
4. **Report Draft & Approval (`/report-drafts/[reportDraftId]`)**: consolidates evidence, inspection results, and approval decisions.
5. **Audit Console (`/audit-events`)**: exposes tenant-scoped audit history for sensitive workflow events.

## Known Product Completeness Gaps

The current app shell exposes navigation items whose hub pages are not yet implemented. These are tracked as product completeness gaps and must be closed by upcoming implementation PRs:

- **Equipment**: visible navigation points to `/equipment`, but the route is missing.
- **Active Incidents**: visible navigation currently points to `/incidents`, while the required route is `/active-incidents`; the hub route is missing.
- **Checklists**: detail route exists, but `/checklists` list/hub route is missing.
- **Approvals**: report detail route exists, but `/approvals` queue route is missing.
- **Settings**: visible navigation points to `/settings`, but the route is missing.

See:

- `docs/11_operational_workflow_guide.md`
- `docs/12_product_requirements_v1.md`
- `docs/13_module_traceability_matrix.md`
- `docs/14_industrial_quality_gate.md`
- `docs/15_implementation_roadmap_v2.md`

## Architecture

- **Frontend (Next.js)**: industrial operations UI built with TypeScript, Tailwind CSS, and route-based workflow pages.
- **Backend (FastAPI)**: authenticated API for equipment knowledge, diagnosis sessions, deterministic analysis, checklist runs, report approvals, dashboard summary, and audit events.
- **Database (PostgreSQL + pgvector-ready schema)**: tenant-scoped operational tables for users, roles, equipment, alarms, I/O points, EtherCAT devices, diagnosis sessions, agent runs, checklists, reports, approvals, policy violations, and audit events.
- **Deterministic Agent Engine**: rule engine for Load Port / FOUP Clamp / EtherCAT I/O scenarios with evidence links and safety guardrails.

## Repository Structure

- `/apps/web/`: Frontend Next.js application
- `/apps/api/`: Backend FastAPI application
- `/contracts/`: OpenAPI specification (`openapi.yaml`)
- `/db/`: Database schema and seed/migration assets
- `/docs/`: Product requirements, traceability, operational workflow, and quality gate documentation

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
.venv/bin/pytest
```

Repository:

```bash
git diff --check
```

## Current Implemented Modules

- Authentication/RBAC foundation
- Tenant-scoped equipment knowledge API
- Diagnosis session API
- Deterministic agent analysis API
- Checklist runner API and detail workflow
- Report draft and approval API plus detail workflow
- Dashboard summary API and dashboard page
- Audit console API and audit page

## Next Implementation Direction

PR-20 through PR-27 are defined in `docs/15_implementation_roadmap_v2.md`. The immediate priority is closing visible navigation gaps with real backend list APIs and frontend hub pages while preserving read-only diagnostics, deterministic analysis, human approval, and auditability.
